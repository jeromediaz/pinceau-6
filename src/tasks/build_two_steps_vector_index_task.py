from typing import Dict, Optional, Mapping, Any, TYPE_CHECKING

from llama_index.llms.openai import OpenAI
from pydantic import BaseModel, create_model

from applications.llama_index.index.two_steps.two_steps_vectorindex import (
    TwoStepsVectorIndex,
)
from core.tasks.task import Task
from core.tasks.task_data import TaskDataContract
from core.tasks.types import TaskData

if TYPE_CHECKING:
    from core.context.context import Context

DEFAULT_OUTPUT_VAR = "index"


class BuildTwoStepsVectorIndexTask(Task["BuildTwoStepsVectorIndexTask.InputModel"]):

    class InputModel(BaseModel):
        index_name: str
        es_url: str
        output_var: str = DEFAULT_OUTPUT_VAR

    def __init__(self, **kwargs) -> None:
        copy_kwargs = kwargs.copy()
        self.default_values: Dict[str, str] = {}

        for key in ["index_name", "es_url", "output_var"]:
            value = copy_kwargs.pop(key, None)
            if value and isinstance(value, str):
                self.default_values[key] = value

        super().__init__(**copy_kwargs)

    def required_inputs(self) -> TaskDataContract:
        used_inputs = {**BuildTwoStepsVectorIndexTask.InputModel.model_fields}

        for key in self.default_values.keys():
            if self.default_values[key]:
                used_inputs.pop(key, None)

        valid_param_field: Dict[str, Any] = {
            k: (v.annotation, v) for k, v in used_inputs.items()
        }

        new_model = create_model(
            "BuildTwoStepsVectorIndexTask.InputModel", **valid_param_field
        )

        return TaskDataContract(new_model.model_fields)

    def provided_outputs(
        self, parent_task_output: Optional[TaskDataContract] = None
    ) -> TaskDataContract:
        outputs = {}
        output_var = self.default_values.get("output_var", DEFAULT_OUTPUT_VAR)
        outputs[output_var] = TwoStepsVectorIndex

        self_contract = TaskDataContract(outputs)
        if parent_task_output and self.is_passthrough:
            cpy = parent_task_output.copy()
            cpy.add_all(self_contract)
            return cpy

        return self_contract

    def input_object(
        self, data: Mapping[str, Any]
    ) -> "BuildTwoStepsVectorIndexTask.InputModel":
        return super().input_object({**self.default_values, **data})

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        input_model_object = self.input_object(data_in)

        def lazy_index() -> TwoStepsVectorIndex:
            if hasattr(lazy_index, "instance"):
                return getattr(lazy_index, "instance")

            llm = OpenAI(
                temperature=0.7,
                api_key="",  # FIXME
            )

            index = TwoStepsVectorIndex.for_elasticsearch(
                input_model_object.index_name, input_model_object.es_url, llm
            )
            setattr(lazy_index, "instance", index)

            return index

        return {**data_in, input_model_object.output_var: lazy_index}
