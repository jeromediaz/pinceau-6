import asyncio
import inspect
import logging
import weakref
from abc import ABCMeta
from threading import Semaphore
from typing import (
    Optional,
    TYPE_CHECKING,
    Any,
    Mapping,
    Sequence,
    TypeVar,
    Generic,
    cast,
    Type,
    Dict,
)

from pydantic import BaseModel, create_model

from core.callbacks.types import EventSenderObject, EventSender
from core.tasks.graph_element_with_parameters import GraphElementWithParameters
from core.tasks.task_node import TaskNode
from core.tasks.types import (
    ProcessMode,
    TaskData,
    TaskDataAsyncIterator,
    Status,
    TaskEdgeKind,
)

if TYPE_CHECKING:
    from core.context.context import Context
    from core.tasks.task_dag import TaskDAG
    from core.tasks.task_data import TaskDataContract

logger = logging.getLogger(__name__)


class TaskConcurrencyMetaclass(ABCMeta):
    def __new__(mcs, name, bases, dct):
        x = super().__new__(mcs, name, bases, dct)

        if "MAX_CONCURRENCY" not in dct:
            x.MAX_CONCURRENCY = -1

        if x.MAX_CONCURRENCY > 1:
            x.TASK_SEMAPHORE = Semaphore(x.MAX_CONCURRENCY)

        return x


Input = TypeVar("Input", bound="BaseModel")

TaskParam = TypeVar("TaskParam")


class Task(
    GraphElementWithParameters,
    EventSenderObject,
    Generic[Input],
    metaclass=TaskConcurrencyMetaclass,
):
    INPUTS: Mapping[str, Any] = dict()
    OUTPUTS: Mapping[str, Any] = dict()
    UI: list[Any] = []

    _input_model: Type[Input]

    class InputModel(BaseModel):
        pass

    MAX_CONCURRENCY = -1
    TASK_SEMAPHORE: Optional[Semaphore] = None

    def __init__(self, dag=None, is_passthrough=False, **kwargs) -> None:
        kwargs.setdefault("description", f"{self.__class__.__name__} task")
        super().__init__(**kwargs)
        self.is_passthrough = is_passthrough
        kwargs.pop("id", None)
        self._params = kwargs
        from core.tasks.task_dag import TaskDAG

        final_dag = dag if dag else TaskDAG.get_dag()
        self.dag = weakref.ref(final_dag)

        if kwargs.get("_register_task", True):
            final_dag.register_task(self)

        self._max_concurrent_tasks = kwargs.get("max_concurrency", self.MAX_CONCURRENCY)

        self._semaphore = None

        self._input_model = cast(Type[Input], self.process_input_model())

        self._process_mode: ProcessMode

        if type(self)._process != Task._process:
            self._process_mode = ProcessMode.NORMAL
        elif type(self)._generator_process != Task._generator_process:
            self._process_mode = ProcessMode.GENERATOR
        else:
            raise NotImplementedError(
                f"{self.__class__.__name__} must implement either _process or _generator_process"
            )

        self._is_conditional_out = type(self).tasks_after != Task.tasks_after

        self._data: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    @property
    def is_conditional_out(self) -> bool:
        return self._is_conditional_out

    async def get_lock(self):
        logger.debug("task %s get_lock", self.id)
        await self._lock.acquire()

    def release_lock(self):
        logger.debug("task %s release_lock", self.id)
        self._lock.release()

    @property
    def process_mode(self) -> ProcessMode:
        return self._process_mode

    @property
    def params(self) -> Mapping[str, Any]:
        dag_object = self.dag()
        if not dag_object:
            raise ValueError("Task does not have a dag object")

        dag_id = dag_object.id

        return self._params_for_dag_and_key(dag_id, self.id)

    def merge_params_input_models(self) -> Optional[Type[BaseModel]]:
        if not hasattr(self.__class__, "Parameters"):
            if hasattr(self.__class__, "parameters_factory"):
                class_param = getattr(self, "parameters_factory")()
            else:
                return None
        else:
            class_param = getattr(self.__class__, "Parameters")

        param_fields = class_param.model_fields
        input_model_class = self.process_input_model()
        input_fields = input_model_class.model_fields

        param_values = self.params

        final_fields: Dict[str, Any] = {}
        for key, value in param_fields.items():
            if key in param_values or key not in input_fields:
                final_fields[key] = (value.annotation, value)

            elif key in input_fields:
                input_field = input_fields[key]
                final_fields[key] = (input_field.annotation, input_field)

        return create_model("RequiredParams", **final_fields)

    def merge_params(self, input_data: Mapping[str, Any]) -> Optional[BaseModel]:
        params_base_model = self.merge_params_input_models()
        if params_base_model is None:
            return None

        merged_values = {**input_data, **self.params}

        return params_base_model.model_validate(merged_values)

    def serialize(self) -> Mapping[str, Any]:
        return {
            "_meta": {
                "id": self.id,
                "module": self.__class__.__module__,
                "class": self.__class__.__name__,
                "dag": self.dag_id or "",
                "passthrough": self.is_passthrough,
            },
            "_params": self.params,  # params and not _params
        }

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> "Task":
        meta = data["_meta"]

        is_passthrough = meta["passthrough"]
        task_id = meta["id"]

        params = data["_params"]

        dag = None
        return cls(id=task_id, is_passthrough=is_passthrough, dag=dag, **params)

    def process_input_model(self) -> Type[Input]:
        return cast(Type[Input], self.__class__.InputModel)

    def input_object(self, data: Mapping[str, Any]) -> Input:
        if hasattr(self._input_model, "model_validate"):
            return self._input_model.model_validate(data)
        else:
            return self._input_model.parse_obj(data)

    def clone(self, **kwargs) -> "Task":

        other_params = {}
        if "id" in kwargs and "id" not in self._params:
            other_params["id"] = kwargs.pop("id")

        return self.__class__(
            is_passthrough=self.is_passthrough, **self._params, **other_params
        )

    @property
    def node(self) -> Optional["TaskNode"]:
        work_dag = self.dag()
        return work_dag.task_node_map[self.id] if work_dag else None

    @property
    def event_source(self) -> EventSender:
        return EventSender("task", self.id)

    def required_params(self) -> Optional[Type[BaseModel]]:
        if not hasattr(self.__class__, "Parameters"):
            if hasattr(self.__class__, "parameters_factory"):
                class_param = getattr(self, "parameters_factory")()
            else:
                return None
        else:
            class_param = getattr(self.__class__, "Parameters")

        if class_param and issubclass(class_param, BaseModel):
            # TODO : remove params already provided at DAG or task level
            all_model_fields = class_param.model_fields

            all_model_fields_keys = set(all_model_fields.keys())
            params_keys = set(self._params.keys())

            intersect = bool(all_model_fields_keys & params_keys)
            if not intersect:
                return class_param

            valid_param_field: Dict[str, Any] = {
                k: (v.annotation, v)
                for k, v in all_model_fields.items()
                if k in self._params
            }
            valid_param_values = {
                k: v for k, v in self._params.items() if k in all_model_fields
            }

            valid_param = create_model("ValidParams", **valid_param_field)

            valid_param.model_validate(valid_param_values)

            new_model_fields = {
                k: (v.annotation, v)
                for k, v in all_model_fields.items()
                if k not in self._params
            }

            if not new_model_fields:
                return None

            return create_model("RequiredParams", **new_model_fields)  # type: ignore

        return None

    def required_inputs(self) -> "TaskDataContract":
        from core.tasks.task_data import TaskDataContract

        if hasattr(self.__class__, "InputModel"):
            input_model_class = self.__class__.InputModel
            return TaskDataContract(input_model_class.model_fields)

        return TaskDataContract(self.INPUTS)

    def provided_outputs(
        self, parent_task_output: Optional["TaskDataContract"] = None
    ) -> "TaskDataContract":
        from core.tasks.task_data import TaskDataContract

        if hasattr(self.__class__, "OutputModel"):
            output_model_class = self.__class__.OutputModel
            if hasattr(output_model_class, "model_fields"):
                self_contract = TaskDataContract(output_model_class.model_fields)
            else:
                # pydantic v1
                self_contract = TaskDataContract(self.__class__.OutputModel.__fields__)
        else:
            self_contract = TaskDataContract(self.OUTPUTS)

        if parent_task_output and self.is_passthrough:
            cpy = parent_task_output.copy()
            cpy.add_all(self_contract)
            return cpy

        return self_contract

    @staticmethod
    def merge_data_in(*data_in_list: Mapping[str, Any]) -> Mapping[str, Any]:
        result: dict[str, Any] = {}
        for data_in in data_in_list:
            result.update({**data_in})

        return result

    def tasks_after(
        self, node: TaskNode, for_mode: TaskEdgeKind = TaskEdgeKind.DEFAULT
    ) -> Sequence[str]:
        return [sub_node.to_id for sub_node in node.usable_sub_nodes(for_mode=for_mode)]

    def _get_semaphore(self) -> Optional[Semaphore]:
        """Get a semaphore from the task class

        Returns:
            Optional[Semaphore]: the defined semaphore or None
        """
        return self.__class__.TASK_SEMAPHORE

    async def process(
        self, context: "Context", data_in: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        semaphore = self._get_semaphore()
        sem_acquired = False

        try:
            if semaphore:
                semaphore.acquire()
                sem_acquired = True

            value = await self._process(context, data_in)
        except Exception as e:
            print(e)
            raise e
        finally:
            if semaphore and sem_acquired:
                semaphore.release()

        return value

    async def _generator_process_before(
        self, context: "Context", data_in: TaskData
    ) -> TaskData:
        return data_in

    async def _generator_process_after(
        self, context: "Context", data_in: TaskData
    ) -> TaskData:
        return data_in

    async def generator_process_before(
        self, context: "Context", data_in: TaskData
    ) -> TaskData:

        value = await self._generator_process_before(context, data_in)

        return value

    async def generator_process_after(
        self, context: "Context", data_in: TaskData
    ) -> TaskData:
        value = await self._generator_process_after(context, data_in)

        return value

    async def generator_process(
        self, context: "Context", data_in: TaskData
    ) -> TaskDataAsyncIterator:
        semaphore = self._get_semaphore()
        sem_acquired = False

        try:
            if semaphore:
                semaphore.acquire()
                sem_acquired = True

            value = self._generator_process(context, data_in)

        except Exception as e:
            raise e
        finally:
            if semaphore and sem_acquired:
                semaphore.release()

        return value

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        raise NotImplementedError

    async def _generator_process(
        self, context: "Context", data_in: TaskData
    ) -> TaskDataAsyncIterator:
        await asyncio.sleep(0)

        yield {}

    def __add_sub_node(self, other: "Task", edge_kind: TaskEdgeKind) -> "Task":
        if not isinstance(other, Task):
            raise ValueError("Right operand of Task >> must also be a task")

        from core.tasks.task_dag import TaskDAG

        dag = TaskDAG.get_dag()

        if not dag:
            raise ValueError("Not inside a DAG context")

        dag.add_child_task(self, other, edge_type=edge_kind)

        return other

    def __lshift__(self, other: TaskParam) -> TaskParam:
        if isinstance(other, Task):
            return cast(TaskParam, other.__add_sub_node(self, TaskEdgeKind.DEFAULT))

        elif isinstance(other, list):
            if all((isinstance(sub_task, Task) for sub_task in other)):
                return cast(
                    TaskParam,
                    [
                        sub_task.__add_sub_node(self, TaskEdgeKind.DEFAULT)
                        for sub_task in other
                    ],
                )

        raise ValueError("Bad parameter")

    def __rshift__(self, other: TaskParam) -> TaskParam:
        if isinstance(other, Task):
            return cast(TaskParam, self.__add_sub_node(other, TaskEdgeKind.DEFAULT))

        elif isinstance(other, list):
            if all((isinstance(sub_task, Task) for sub_task in other)):
                return cast(
                    TaskParam,
                    [
                        self.__add_sub_node(sub_task, TaskEdgeKind.DEFAULT)
                        for sub_task in other
                    ],
                )

        raise ValueError("Bad parameter")

    def __rrshift__(self, other: TaskParam) -> TaskParam:
        return self.__lshift__(other)

    def __rlshift__(self, other: TaskParam) -> TaskParam:
        return self.__rshift__(other)

    def __xor__(self, other) -> "Task":
        return self.__add_sub_node(other, TaskEdgeKind.LOOP_START)

    def __and__(self, other) -> "Task":
        return self.__add_sub_node(other, TaskEdgeKind.LOOP_END)

    async def set_status(
        self,
        context: "Context",
        value: "Status",
        /,
        *,
        error: Optional[Exception] = None,
        send_value: bool = True,
        **kwargs,
    ):
        logger.debug("%s set_status %s", self.id, value)
        await context.event(
            self,
            "status",
            {"id": self.full_id, "status": value, "error": error},
        )

        super().set_status(context, value, error=error, **kwargs)

    def get_field_ui(self):
        class_ui = getattr(self.__class__, "UI")

        if not class_ui:
            return []

        if inspect.isclass(class_ui) and issubclass(class_ui, BaseModel):
            from core.tasks.task_data import TaskDataContract

            task_contract = TaskDataContract(class_ui.model_fields)

            values = []
            for field_id, field_dict in task_contract.fields_map(for_task=self).items():
                source = field_dict.get("source", field_id)

                if source is not False:
                    field_dict["source"] = f"{self.full_id}::{source}"
                else:
                    del field_dict["source"]

                values.append(field_dict)

            return values

        if isinstance(class_ui, list):
            return [{**item, "task": self.full_id} for item in class_ui]

    def get_ui(self):
        class_ui = getattr(self.__class__, "UI")

        if not class_ui:
            return []

        if inspect.isclass(class_ui) and issubclass(class_ui, BaseModel):
            from core.tasks.task_data import TaskDataContract

            task_contract = TaskDataContract(class_ui.model_fields)

            values = [
                {**field_dict, "id": field_id, "task": self.full_id}
                for field_id, field_dict in task_contract.fields_map().items()
            ]

            return values

        if isinstance(class_ui, list):
            return [{**item, "task": self.full_id} for item in class_ui]

    @property
    def dag_id(self) -> str:
        dag_instance = self.dag()
        return dag_instance.id if dag_instance else None

    @property
    def full_id(self) -> str:
        return f"{self.dag_id}::{self.id}"

    @property
    def data(self):
        return self._data

    def set_data(self, key: str, value: Any):
        self._data[key] = value

    def get_values_payload(self):
        data_list = []

        task_id = self.full_id

        for key, value in self.data.items():
            data_list.append({"task": task_id, "id": key, **value})

        return data_list

    async def set_progress(self, context: "Context", progress: float):

        work_dag: Optional[TaskDAG] = self.dag()
        if work_dag:
            await work_dag.set_progress(
                context,
                progress,
            )
