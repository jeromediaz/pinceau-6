from typing import Mapping, Any, TYPE_CHECKING, cast

from pydantic import BaseModel

from core.context.composite_context import CompositeContext
from misc.mongodb_helper import mongodb_collection
from tasks.alpaca_llm_task import AlpacaLlmTask

if TYPE_CHECKING:
    from core.context.context import Context


class LoggedAlpacaLlmTask(AlpacaLlmTask):

    class InputModel(BaseModel):
        input: str
        instruction: str = ""
        answer: str = ""
        log_info: dict = {}
        mongodb_database: str

    async def _process(self, context: "Context", data_input: Mapping[str, Any]):
        if not isinstance(context, CompositeContext):
            raise ValueError(
                f"{self.__class__.__name__} context should be a CompositeContext"
            )

        data_input_object = self.input_object(data_input)
        llm_input = {
            "input": data_input_object.input,
            "instruction": data_input_object.instruction,
            "answer": data_input_object.answer,
        }
        log_info = data_input_object.log_info

        result = cast(Mapping[str, Any], await super().process(context, llm_input))

        llm_input.update(result)

        collection = mongodb_collection(
            context, "mongodb", data_input_object.moongodb_database, "alpaca_llm_log"
        )

        data_object = {**llm_input, **result, **log_info}
        collection.insert_one(data_object)

        return result
