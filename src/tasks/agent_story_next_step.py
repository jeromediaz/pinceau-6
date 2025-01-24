import re
from typing import TYPE_CHECKING, cast, Mapping, Any

from pydantic import BaseModel

from core.context.context import Context
from core.tasks.task import Task
from misc.mongodb_helper import mongodb_collection
from tasks.agent_context_character import AgentContextCharacter
from tasks.agent_story_update_event import AgentStoryUpdateEvent
from tasks.logged_alpaca_llm_task import LoggedAlpacaLlmTask

if TYPE_CHECKING:
    from core.context.composite_context import CompositeContext
    from core.tasks.types import JSONParam


class AgentStoryNextStep(Task):
    class InputModel(BaseModel):
        event: str
        character: str
        mongodb_database: str

    class OutputModel(BaseModel):
        instruction: str
        end_word: str

    async def _process(
        self, context: "Context", input_data: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        if not isinstance(context, CompositeContext):
            raise ValueError(
                f"{self.__class__.__name__} context should be a CompositeContext"
            )

        input_model_object = self.input_object(input_data)

        agent_context_character = AgentContextCharacter()
        agent_story_update_event = AgentStoryUpdateEvent()

        steps_log_collection = mongodb_collection(
            context,
            "mongodb",
            input_model_object.mongodb_database,
            f"{input_model_object.character}_steps_log",
        )

        def log(s: int, operation: str, data: "JSONParam"):
            steps_log_collection.insert_one(
                {
                    "step": s,
                    "operation": operation,
                    "data": data,
                    "generation": self.id,
                }
            )
            return s + 1

        step = 0
        step = log(step, "character_fetch", cast("JSONParam", input))

        llm_task = LoggedAlpacaLlmTask()

        work_input = {**input_data}

        loop = True

        full_answer = ""
        end_word = "<FINISHED>"

        work_input_map = cast(
            Mapping[str, Any],
            await agent_context_character.process(context, work_input),
        )

        work_input = {**work_input_map}
        step = log(step, "agent_context_character", work_input)

        while loop:
            llm_input = {
                "instruction": f"{work_input.get('character_instruction')}\n\nFrom the given situation, make the story slowly advance until the final goal is reached. When the final goal is reached say '<FINISHED>'.",
                "input": work_input.get("event"),
            }

            llm_task_output = cast(
                Mapping[str, Any], await llm_task.process(context, llm_input)
            )
            answer: str = cast(str, llm_task_output["text"])

            if not answer or step >= 20:
                loop = False
            elif answer.rstrip().endswith(end_word):
                answer = answer.rstrip()[: len(end_word) * -1].rstrip()
                loop = False

            full_answer += answer

            if not loop:
                break

            work_input["last_answer"] = answer

            paragraphs = re.split(r"\n\s\n", answer)
            work_input["answer"] = "\n\n".join(paragraphs[-2:])

            step = log(step, "last_answer", work_input)

            work_input_map = cast(
                Mapping[str, Any],
                await agent_story_update_event.process(
                    context, cast(Mapping[str, Any], work_input)
                ),
            )

            step = log(
                step, "agent_story_update_event", cast("JSONParam", work_input_map)
            )

            work_input = {**work_input_map}

        collection = mongodb_collection(
            context,
            "mongodb",
            input_model_object.mongodb_database,
            f"{input_model_object.character}_log",
        )

        collection.insert_one(
            {
                "event": input_model_object.event,
                "text": full_answer,
                "generation": self.id,
            }
        )

        return {**work_input}
