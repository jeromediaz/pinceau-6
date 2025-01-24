from typing import TYPE_CHECKING, Mapping, Any, cast

from pydantic import BaseModel

from core.tasks.task import Task
from tasks.alpaca_llm_task import AlpacaLlmTask

if TYPE_CHECKING:
    from core.context.context import Context


class AgentStoryUpdateEvent(Task):

    class InputModel(BaseModel):
        event: str
        last_answer: str = ""

    class OutputModel(BaseModel):
        instruction: str
        end_word: str

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        input_model_object = self.input_object(data_input)

        llm_task = AlpacaLlmTask()

        input_val = f"{input_model_object.event}\n\n{input_model_object.last_answer}"

        llm_task_input = {
            "instruction": "Write a concise version of the current context. Focus on where are the characters, what they are wearing.",
            "input": input_val,
        }

        llm_task_output = cast(
            Mapping[str, Any], await llm_task.process(context, llm_task_input)
        )

        return {**data_input, "event": llm_task_output["text"]}
