import copy
import math
from enum import Enum
from typing import Optional, Any, TYPE_CHECKING, Type, Tuple, Dict, cast

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from core.tasks.task import Task
from core.tasks.task_data import TaskDataContract
from core.tasks.types import TaskData, TaskDataAsyncIterator
from ui.helper import P6Field, FieldOptions

if TYPE_CHECKING:
    from core.context.context import Context


class TestEnum(Enum):
    case_1 = 1
    case_2 = 2


class RangeTask(Task["RangeTask.InputModel"]):

    class InputModel(BaseModel):
        start: int
        end: int
        step: int = 1
        expected_iterations: int = 1

    class Parameters(BaseModel):
        varname: str = P6Field(options=FieldOptions.FULL_WIDTH)
        start: int
        end: int
        step: int = 1

    def __init__(self, **kwargs):
        kwargs.setdefault("is_passthrough", True)
        super().__init__(**kwargs)

    def clone(self, **kwargs) -> "Task":
        copy_params = {**self.params}
        copy_params.update(kwargs)
        return self.__class__(**copy_params)

    def process_input_model(self) -> Type["RangeTask.InputModel"]:
        params = self.params
        varname = params["varname"]

        model_fields = copy.deepcopy(self.__class__.InputModel.model_fields)
        model_fields["start"].validation_alias = f"{varname}_start"
        model_fields["end"].validation_alias = f"{varname}_end"
        model_fields["step"].validation_alias = f"{varname}_step"

        model_fields["start"].default = params.get("start")
        model_fields["end"].default = params.get("end")
        model_fields["step"].default = params.get("step", 1)

        dynamic_model_fields: Dict[str, Tuple[type[Any] | None, FieldInfo]] = {}
        for field_key, field_info in model_fields.items():
            dynamic_model_fields[field_key] = (field_info.annotation, field_info)

        return cast(
            Type[RangeTask.InputModel],
            create_model("InputModelDynamic", **dynamic_model_fields),  # type: ignore
        )

    def required_inputs(self) -> TaskDataContract:
        dependency: dict[str, Type | Tuple[Type, bool] | FieldInfo] = dict()

        params = self.params
        varname = params["varname"]

        if "start" not in params:
            dependency[f"{varname}_start"] = int
        if "end" not in params:
            dependency[f"{varname}_end"] = int
        if "step" not in params:
            dependency[f"{varname}_step"] = FieldInfo.from_annotated_attribute(int, 1)

        return TaskDataContract(dependency)

    def provided_outputs(
        self, parent_task_output: Optional[TaskDataContract] = None
    ) -> TaskDataContract:
        provide = {"expected_iterations": int}

        params = self.params
        varname = params["varname"]

        provide[varname] = int

        self_contract = TaskDataContract(provide)
        if parent_task_output and self.is_passthrough:
            cpy = parent_task_output.copy()
            cpy.add_all(self_contract)
            return cpy

        return self_contract

    async def _generator_process(
        self, context: "Context", data: TaskData
    ) -> TaskDataAsyncIterator:
        input_data = self.input_object(data)
        start = input_data.start
        end = input_data.end
        step = input_data.step
        expected_iterations = input_data.expected_iterations * math.floor(
            (end - start) / step
        )

        merged_params = cast(RangeTask.Parameters, self.merge_params(data))
        varname = merged_params.varname

        for i in range(start, end, step):
            output = {
                **data,
                varname: i,
                "expected_iterations": expected_iterations,
            }
            yield output
