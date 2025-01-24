from typing import Mapping, Any, TYPE_CHECKING

from pydantic import BaseModel

from core.context.composite_context import CompositeContext
from core.tasks.task import Task
from misc.mongodb_helper import mongodb_collection

if TYPE_CHECKING:
    from core.context.context import Context


class AgentCharacter(Task["AgentCharacter.InputModel"]):

    class InputModel(BaseModel):
        character: str
        event: str
        mongodb_database: str

    class OutputModel(BaseModel):
        character: str
        name: str
        description: str

    async def _process(
        self, context: "Context", input_data: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        if not isinstance(context, CompositeContext):
            raise ValueError(
                f"{self.__class__.__name__} context should be a CompositeContext"
            )

        input_model_object = self.input_object(input_data)

        collection = mongodb_collection(
            context, "mongodb", input_model_object.mongodb_database, "characters"
        )
        data = collection.find_one({"key": input_model_object.character})
        character = input_model_object.character

        output = {
            **input_data,
            f"{character}_name": data.get("name"),
            f"{character}_description": data.get("description"),
        }

        return output
