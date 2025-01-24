import re
from typing import TYPE_CHECKING, Mapping, Any, cast

from pydantic import BaseModel

from core.context.composite_context import CompositeContext
from core.tasks.task import Task
from misc.mongodb_helper import mongodb_collection
from tasks.alpaca_llm_task import AlpacaLlmTask

if TYPE_CHECKING:
    from core.context.context import Context


class AgentTask(Task):
    class InputModel(BaseModel):
        event: str
        agent: str
        mongodb_database: str

    class OutputModel(BaseModel):
        agent: str
        event: str
        answer: str

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        if not isinstance(context, CompositeContext):
            raise ValueError(
                f"{self.__class__.__name__} context should be a CompositeContext"
            )

        llm_task = AlpacaLlmTask(dag=self.dag())

        input_model_object = self.input_object(data_input)

        collection = mongodb_collection(
            context,
            "mongodb",
            input_model_object.mongodb_database,
            "agent_instructions",
        )

        agent = collection.find_one({"key": input_model_object.agent})

        end_word = agent.get("end_word")

        llm_task_input = {
            "instruction": agent.get("instruction"),
            "input": input_model_object.event,
        }
        full_answer = ""

        loop = True
        while loop:
            llm_task_output = cast(
                Mapping[str, Any], await llm_task.process(context, llm_task_input)
            )
            answer: str = llm_task_output["text"]

            if not answer:
                loop = False
            elif answer.rstrip().endswith(end_word):
                answer = answer.rstrip()[: len(end_word) * -1].rstrip()
                loop = False

            full_answer += answer

            paragraphs = re.split(r"\n\s\n", answer)
            answer = "\n\n".join(paragraphs[-2:])
            llm_task_input["answer"] = answer

        print("AGENT TASK END")

        return {
            "agent": input_model_object.agent,
            "event": input_model_object.event,
            "answer": full_answer.strip().rstrip(),
            "mongodb_database": input_model_object.mongodb_database,
        }
