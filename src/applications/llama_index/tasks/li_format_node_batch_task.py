from typing import List, Mapping, Any, TYPE_CHECKING, cast, Optional

from llama_index.core.indices.utils import default_format_node_batch_fn
from llama_index.core.schema import NodeWithScore, BaseNode
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context
    from core.tasks.task_data import TaskDataContract


class LiFormatNodeBatchTask(Task):

    class Parameters(BaseModel):
        input_name: str = "results"
        output_name: str = "result"

    def required_inputs(self) -> "TaskDataContract":
        from core.tasks.task_data import TaskDataContract

        params = cast(LiFormatNodeBatchTask.Parameters, self.merge_params({}))

        fields: Mapping[str, Any] = {
            params.input_name: (List[NodeWithScore], FieldInfo())
        }

        model_class = create_model("LiFormatNodeBatchTask.InputModel", **fields)
        return TaskDataContract(model_class.model_fields)

    def provided_outputs(
        self, parent_task_output: Optional["TaskDataContract"] = None
    ) -> "TaskDataContract":
        from core.tasks.task_data import TaskDataContract

        params = cast(LiFormatNodeBatchTask.Parameters, self.merge_params({}))

        fields: Mapping[str, Any] = {params.output_name: (str, FieldInfo())}

        model_class = create_model("LiFormatNodeBatchTask.InputModel", **fields)
        return TaskDataContract(model_class.model_fields)

    async def _process(
        self, context: "Context", input_data: Mapping[str, Any]
    ) -> Mapping[str, Any]:

        param_object = cast(
            LiFormatNodeBatchTask.Parameters, self.merge_params(input_data)
        )
        nodes = cast(List[BaseNode], input_data.get(param_object.input_name))

        as_string = default_format_node_batch_fn(nodes)

        return {param_object.output_name: as_string}
