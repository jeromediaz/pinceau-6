from typing import TYPE_CHECKING, Mapping, Any

from pydantic import BaseModel

from core.context.composite_context import CompositeContext
from core.tasks.task import Task
from misc.mongodb_helper import mongodb_collection

if TYPE_CHECKING:
    from core.context.context import Context


class AgentLog(Task):

    class InputModel(BaseModel):
        event: str
        agent: str
        answer: str
        mongodb_answer: str

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:

        if not isinstance(context, CompositeContext):
            raise ValueError(
                f"{self.__class__.__name__} context should be a CompositeContext"
            )

        data_input_object = self.input_object(data_input)

        mongodb_database = data_input_object.mongodb_database
        if not mongodb_database:
            raise ValueError("Missing mongodb_database input")

        print(f"Process agent log {mongodb_database}")
        collection = mongodb_collection(
            context, "mongodb", mongodb_database, f"{data_input_object.agent}_log"
        )

        collection.insert_one(
            {"event": data_input_object.event, "answer": data_input_object.answer}
        )

        return {**data_input}
