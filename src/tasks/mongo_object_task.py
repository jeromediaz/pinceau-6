from typing import TypeAlias, TYPE_CHECKING, Mapping, Any, Optional, Dict, Type, cast

from bson import ObjectId
from pydantic import BaseModel, create_model, Field

from core.context.composite_context import CompositeContext
from core.context.global_context import GlobalContext
from core.database.mongodb import MongoDBHandler
from core.tasks.task import Task
from core.tasks.task_data import TaskDataContract
from misc.mongodb_helper import mongodb_collection

if TYPE_CHECKING:
    from core.context.context import Context

reference: TypeAlias = str


class MongoObjectTask(Task):

    class InputModel(BaseModel):
        object_id: str

    class OutputModel(BaseModel):
        model_object: BaseModel

    class _Parameters(BaseModel):
        fixed_object_id: str = ""
        input_name: str = "object_id"
        output_name: str = "model_object"

    def parameters_factory(self) -> Type[BaseModel]:

        final_fields: Dict[str, Any] = {
            "fixed_object_id": (
                str,
                Field(
                    "",
                    json_schema_extra={
                        "type": "reference",
                        "reference": f"data/mongodb/{self._source}",
                        "optional": True,
                        "opts": ["fullWidth"],
                    },
                ),
            ),
            "input_name": (str, Field("object_id")),
            "output_name": (str, Field("model_object")),
        }

        return create_model("Parameters", **final_fields)

    def required_inputs(self) -> TaskDataContract:

        dependency: Dict[str, Any] = dict()

        # TODO: handle reference with restriction

        params = cast(MongoObjectTask._Parameters, self.merge_params({}))

        if params.fixed_object_id:
            # we take the value from the parameter
            return TaskDataContract({})

        dependency[params.input_name] = {
            "type": ("reference", str),
            "reference": f"data/mongodb/{self._source}",
        }

        if self._model != self._source:
            dependency["object_id"]["model"] = self._model

            global_context = GlobalContext.get_instance()
            model_description = global_context.models_manager.get_model(self._model)
            allowed_models = [self._model]
            if model_description:
                for sub_model in model_description.flat_sub_models:
                    allowed_models.append(sub_model.name)

            dependency["object_id"]["filter"] = {"_model": allowed_models}

        return TaskDataContract(dependency)

    def provided_outputs(
        self, parent_task_output: Optional["TaskDataContract"] = None
    ) -> "TaskDataContract":

        outputs = {}
        params = cast(MongoObjectTask._Parameters, self.merge_params({}))
        outputs[params.output_name] = BaseModel

        self_contract = TaskDataContract(outputs)
        if parent_task_output and self.is_passthrough:
            cpy = parent_task_output.copy()
            cpy.add_all(self_contract)
            return cpy

        return self_contract

    def __init__(
        self, source: str, model: Optional[str] = None, handler=None, **kwargs
    ):
        kwargs.pop("is_passthrough", None)
        super().__init__(is_passthrough=True, **kwargs)
        self._handler = handler
        self._source = source
        self._model = model if model else source

    def clone(self, **kwargs) -> "Task":
        return self.__class__(
            self._source, self._model, handler=self._handler, **self.params, **kwargs
        )

    def serialize(self) -> Mapping[str, Any]:
        parent = {**super().serialize(), "_source": self._source, "_model": self._model}

        if self._handler:
            parent["_handler"] = {
                "module": self._handler.__module__,
                "name": self._handler.__name__,
            }

        return parent

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> "Task":
        meta = data["_meta"]
        task_id = meta["id"]
        source = data["_source"]
        model = data["_model"]
        handler_data = data["_handler"]

        if handler_data:
            module = __import__(handler_data["module"], fromlist=[""])
            handler = getattr(module, handler_data["name"])
        else:
            handler = None

        params = data["_params"]

        dag = None
        return cls(
            source,
            id=task_id,
            model=model,
            handler=handler,
            dag=dag,
            **params,
        )

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:

        params = cast(MongoObjectTask._Parameters, self.merge_params(data_input))

        if not isinstance(context, CompositeContext):
            raise ValueError(
                f"{self.__class__.__name__} context should be a CompositeContext"
            )

        mongo_object = (
            params.fixed_object_id
            if params.fixed_object_id
            else data_input[params.input_name]
        )
        mongo_collection = mongodb_collection(
            context, "mongodb", "pinceau6", self._source
        )

        value = mongo_collection.find_one({"_id": ObjectId(mongo_object)})

        model_object = MongoDBHandler.load_object(value)

        # TODO: add security to ensure we have an instance of the correct type

        if not self._handler:
            return {**data_input, params.output_name: model_object}

        return self._handler(self, context, **data_input, model_object=model_object)
