import copy
from typing import TYPE_CHECKING, Mapping, Any, Optional, Type, Dict, cast

from pydantic import BaseModel, create_model, Field

from core.context.composite_context import CompositeContext
from core.tasks.task import Task
from misc.mongodb_helper import mongodb_collection

if TYPE_CHECKING:
    from core.context.context import Context
    from core.tasks.task_data import TaskDataContract


class AgentMongoDBUpsert(Task):

    class Parameters(BaseModel):
        collection: Optional[str] = None
        database: Optional[str] = None
        db_link: str = Field(default="mongodb")

    class InputModel(BaseModel):
        collection: str = "test"
        data: dict
        database: str = "test"

    class OutputModel(BaseModel):
        result: bool

    def process_input_model(self) -> Type["AgentMongoDBUpsert.InputModel"]:
        params = self.params

        model_fields = copy.deepcopy(self.__class__.InputModel.model_fields)

        if params.get("collection"):
            del model_fields["collection"]
        if params.get("database"):
            del model_fields["database"]

        dynamic_model_fields: Dict[str, Any] = {}
        for field_key, field_info in model_fields.items():
            dynamic_model_fields[field_key] = (field_info.annotation, field_info)

        return cast(
            Type[AgentMongoDBUpsert.InputModel],
            create_model("InputModelDynamic", **dynamic_model_fields),  # type: ignore
        )

    def required_inputs(self) -> "TaskDataContract":
        from core.tasks.task_data import TaskDataContract

        return TaskDataContract(self.process_input_model().model_fields)

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        if not isinstance(context, CompositeContext):
            raise ValueError(
                f"{self.__class__.__name__} context should be a CompositeContext"
            )

        input_model_object = self.input_object(data_input)
        params_object = cast(
            AgentMongoDBUpsert.Parameters, self.merge_params(data_input)
        )

        if not params_object.database or not params_object.collection:
            raise ValueError("Missing database and/or collection")

        collection = mongodb_collection(
            context,
            params_object.db_link,
            params_object.database,
            params_object.collection,
        )

        success = False
        try:
            collection.insert_one(input_model_object.data)
            success = True
        except Exception as e:
            print(e)

        return {**data_input, "success": success}
