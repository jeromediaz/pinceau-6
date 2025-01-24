from enum import Flag, auto
from typing import (
    TYPE_CHECKING,
    Optional,
    List,
    Dict,
    Any,
    Mapping,
    Sequence,
    Tuple,
    Type,
)

from pydantic import Field, BaseModel
from pydantic.fields import FieldInfo, _FromFieldInfoInputs, ComputedFieldInfo
from pydantic_core import PydanticUndefined
from typing_extensions import Unpack

from core.models.types import ModelUsageMode
from core.tasks.task_dag import TaskDAG
from core.tasks.task_data import TaskDataContract

if TYPE_CHECKING:
    from core.tasks.task import Task
    from core.context.global_context import GlobalContext


def available_dag_for_model(
    model_name: str, context: "GlobalContext"
) -> Sequence[Tuple[str, bool, "TaskDAG"]]:
    return context.models_manager.get_model_available_dag(
        context.dag_manager, model_name
    )


def ui_fields_from_base_model(
    model_class: Type[BaseModel],
    *,
    for_task: Optional["Task"] = None,
    display_mode=ModelUsageMode.DEFAULT,
) -> List[Dict[str, Any]]:
    full_dict: Dict[str, FieldInfo | ComputedFieldInfo] = {
        **model_class.model_fields,
        **model_class.model_computed_fields,
    }

    model_contract = TaskDataContract(full_dict)

    model_contract_fields_map = model_contract.fields_map(for_task=for_task, display_mode=display_mode)

    hidden_fields = (
        model_class.hidden_fields(display_mode=display_mode)
        if hasattr(model_class, "hidden_fields")
        else set()
    )

    fields = []
    for field_id, field_map in model_contract_fields_map.items():
        if field_id in hidden_fields:
            continue

        field_dict = dict(field_map)

        source = field_dict.get("source", field_id)
        if source is not False:
            field_dict["source"] = (
                f"{for_task.full_id}::{source}" if for_task else source
            )
        else:
            del field_dict["source"]

        fields.append(field_dict)

    return fields


def safe_add_str_to_list(the_list: List[str], value: str):
    if value not in the_list:
        the_list.append(value)


class FieldOptions(Flag):
    READ_ONLY = auto()
    DISABLED = auto()
    FULL_WIDTH = auto()
    MULTILINE = auto()
    HIDE_ON_LIST = auto()
    OPTIONAL = auto()
    MULTIPLE = auto()

    def as_json_extra(
        self, original_value: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        result = {} if not original_value else dict(original_value)

        if self.contains_one_of(
            FieldOptions.READ_ONLY, FieldOptions.FULL_WIDTH, FieldOptions.MULTILINE
        ):
            opts = result.setdefault("opts", [])

            if FieldOptions.READ_ONLY in self:
                safe_add_str_to_list(opts, "readOnly")
            if FieldOptions.DISABLED in self:
                safe_add_str_to_list(opts, "disabled")
            if FieldOptions.FULL_WIDTH in self:
                safe_add_str_to_list(opts, "fullWidth")
            if FieldOptions.MULTILINE in self:
                safe_add_str_to_list(opts, "multiline")

        if self.contains_one_of(FieldOptions.HIDE_ON_LIST):
            hide_on = result.setdefault("hideOn", [])

            if FieldOptions.HIDE_ON_LIST in self:
                safe_add_str_to_list(hide_on, "list")

        if FieldOptions.OPTIONAL in self:
            result["optional"] = True

        if FieldOptions.MULTIPLE in self:
            result["multiple"] = True

        return result

    def contains_one_of(self, *check_values: "FieldOptions") -> bool:
        return any((check_value in self for check_value in check_values))


class P6FieldInfo(FieldInfo):

    @staticmethod
    def from_field(
        default: Any = PydanticUndefined, **kwargs: Unpack[_FromFieldInfoInputs]
    ) -> "P6FieldInfo":

        if "annotation" in kwargs:
            raise TypeError('"annotation" is not permitted as a Field keyword argument')
        return P6FieldInfo(default=default, **kwargs)

    @classmethod
    def from_field_info(cls, field_info: FieldInfo) -> "P6FieldInfo":
        kwargs: Dict[str, Any] = {
            k: v for k, v in field_info.__repr_args__() if isinstance(k, str)
        }
        kwargs.pop("annotation", None)

        return P6FieldInfo.from_field(**kwargs)


def P6Field(*args, options: FieldOptions = FieldOptions(0), **kwargs) -> Any:
    if options.value:
        json_schema_extra = kwargs.setdefault("json_schema_extra", {})
        kwargs["json_schema_extra"] = options.as_json_extra(json_schema_extra)

    return P6FieldInfo.from_field_info(Field(*args, **kwargs))


def P6ReferenceField(
    *args, reference: str, options: FieldOptions = FieldOptions(0), **kwargs
) -> Any:
    json_schema_extra = kwargs.setdefault("json_schema_extra", {})
    if options.value:
        json_schema_extra = options.as_json_extra(json_schema_extra)
    kwargs["json_schema_extra"] = json_schema_extra
    json_schema_extra["type"] = "reference"
    json_schema_extra["reference"] = reference

    if "option_value" in kwargs:
        json_schema_extra["render_optionValue"] = kwargs.pop("option_value")

    return P6FieldInfo.from_field_info(Field(*args, **kwargs))


def WrappedP6Field(
    container_field, *args, options: FieldOptions = FieldOptions(0), **kwargs
) -> Any:
    json_schema_extra = kwargs.setdefault("json_schema_extra", {})
    json_schema_extra["wrapped_in"] = container_field

    kwargs["json_schema_extra"] = options.as_json_extra(json_schema_extra)

    return P6FieldInfo.from_field_info(Field(*args, **kwargs))
