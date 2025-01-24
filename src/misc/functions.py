from typing import Tuple, Optional, TYPE_CHECKING, Type, Dict, Mapping, cast, Any

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

if TYPE_CHECKING:
    from core.tasks.task_dag import TaskDAG
    from core.tasks.task import Task


def strtobool(val: str) -> bool:

    if not isinstance(val, str):
        raise ValueError(f"{val} Not a string ({type(val)})")

    val = val.lower()

    if val in ("y", "yes", "true", "t", "true", "1", "on"):
        return True
    if val in ("n", "no", "false", "f", "0", "off"):
        return False

    raise ValueError("Invalid truth value %r" % (val,))


def extract_dag_id(dag_id: str) -> Tuple[str, str, Optional[str]]:
    dag_split = dag_id.split(":")

    dag_part = dag_split[0]
    job_id = dag_split[1] if len(dag_split) > 1 else None

    if "[" in dag_part:
        square_bracket_index = dag_part.index("[")
        dag_identifier = dag_part[:square_bracket_index]
        dag_variant = dag_part[square_bracket_index + 1 : -1]
    else:
        dag_identifier = dag_part
        dag_variant = "_default_"

    return dag_identifier, dag_variant, job_id


def construct_dag_id(template: str, variant: str = "_default_") -> str:
    return template if variant == "_default_" else f"{template}[{variant}]"


def construct_full_dag_id(
    template: str, variant: str = "_default_", job_id: Optional[str] = None
) -> str:
    dag_id = construct_dag_id(template, variant)

    return dag_id if not job_id else f"{dag_id}:{job_id}"


class DagChatAdaptation:
    def __init__(
        self, input_key: str, input_type: str, output_key: str, output_type: str
    ):
        self._input_key = input_key
        self._input_type = input_type
        self._output_key = output_key
        self._output_type = output_type

    @property
    def input_key(self) -> str:
        return self._input_key

    @property
    def input_type(self) -> str:
        return self._input_type

    @property
    def output_key(self) -> str:
        return self._output_key

    @property
    def output_type(self) -> str:
        return self._output_type


def extract_single_output_model_field_str(task: "Task") -> Optional[Tuple[str, str]]:
    if hasattr(task.__class__, "OutputModel"):
        output_model_class = getattr(task.__class__, "OutputModel")

        if issubclass(output_model_class, BaseModel):
            return extract_single_field_str(output_model_class)

    task_data_contract = task.provided_outputs(None)
    models = create_model(
        "OutputModel", **(cast(Mapping[str, Any], task_data_contract.pydantic_fields()))
    )

    return extract_single_field_str(models)


def extract_single_input_model_field_str(
    task: "Task", ignore_field: Optional[str] = None
) -> Optional[str]:
    input_model_class = dict(task.required_inputs().pydantic_fields())

    if ignore_field:
        input_model_class.pop(ignore_field, None)

    model_fields_keys = list(input_model_class.keys())

    if len(model_fields_keys) != 1:
        return None

    single_field_key = model_fields_keys[0]
    single_field_type, single_field = input_model_class[single_field_key]
    if single_field_type is not str:
        return None

    return single_field_key


def extract_common_single_input_model_field_str(
    dag: "TaskDAG", ignore_field: Optional[str] = None
) -> Optional[Tuple[str, str]]:
    from applications.chat.models.a_chat_message import AChatMessage

    fields = dict(dag.get_required_inputs().pydantic_fields())
    if ignore_field:
        fields.pop(ignore_field, None)

    model_fields_keys = list(fields.keys())

    if len(model_fields_keys) != 1:
        return None

    single_field_key = model_fields_keys[0]
    single_field_type, single_field = fields[single_field_key]

    if single_field_type is str:
        return single_field_key, "str"
    elif issubclass(single_field_type, AChatMessage):
        return single_field_key, "message"

    return None


def extract_single_field_str_from_model_fields(
    model_fields: Dict[str, FieldInfo], ignore_field: Optional[str] = None
) -> Optional[Tuple[str, str]]:
    from applications.chat.models.a_chat_message import AChatMessage

    if ignore_field:
        model_fields.pop(ignore_field, None)

    model_fields_keys = list(model_fields.keys())

    if len(model_fields_keys) != 1:
        return None

    single_field_key = model_fields_keys[0]
    single_field: FieldInfo = model_fields[single_field_key]
    annotation = single_field.annotation
    if not annotation:
        return None
    if annotation is str:
        return single_field_key, "str"
    elif issubclass(annotation, AChatMessage):
        return single_field_key, "message"

    return None


def extract_single_field_str(
    model: Type[BaseModel], ignore_field: Optional[str] = None
) -> Optional[Tuple[str, str]]:
    model_fields = model.model_fields
    return extract_single_field_str_from_model_fields(
        model_fields, ignore_field=ignore_field
    )


def check_if_dag_chat_compatible(
    dag: "TaskDAG", ignore_field: Optional[str] = None
) -> Optional[DagChatAdaptation]:

    leaf_tasks = dag.get_leaf_tasks()

    if len(leaf_tasks) > 1:
        # we can have only one leaf task
        return None

    leaf_task = leaf_tasks[0]

    output_field_name = extract_single_output_model_field_str(leaf_task)

    if not output_field_name:
        return None

    input_field_name = extract_common_single_input_model_field_str(
        dag, ignore_field=ignore_field
    )
    if input_field_name:
        return DagChatAdaptation(
            input_field_name[0],
            input_field_name[1],
            output_field_name[0],
            output_field_name[1],
        )

    return None
