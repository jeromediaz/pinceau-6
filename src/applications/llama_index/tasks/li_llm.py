from typing import Mapping, Any, TYPE_CHECKING, cast

from bson import ObjectId
from pydantic import BaseModel

from applications.llama_index.models.li_llm import LiLlm
from core.database.mongodb import MongoDBHandler
from core.tasks.task import Task
from misc.mongodb_helper import mongodb_collection
from ui.helper import FieldOptions, P6ReferenceField

if TYPE_CHECKING:
    from core.context.context import Context


class LLMPrepareTask(Task["LLMPrepareTask.InputModel"]):

    class Parameters(BaseModel):
        llm_object: str = P6ReferenceField(
            reference="data/mongodb/llamaindex_llm",
            options=FieldOptions.FULL_WIDTH | FieldOptions.OPTIONAL,
        )

    class OutputModel(BaseModel):
        llm_model: LiLlm

    OUTPUTS: Mapping[str, Any] = {"llm_model": LiLlm}

    async def _process(
        self, context: "Context", input_data: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        params_object = cast(LLMPrepareTask.Parameters, self.merge_params(input_data))

        mongo_object_id = params_object.llm_object

        mongo_collection = mongodb_collection(
            context, "mongodb", "pinceau6", "llamaindex_llm"
        )

        value = mongo_collection.find_one({"_id": ObjectId(mongo_object_id)})

        model_object = cast(LiLlm, MongoDBHandler.load_object(value))

        if self.is_passthrough:
            return {"llm_model": model_object, **input_data}

        return {"llm_model": model_object}
