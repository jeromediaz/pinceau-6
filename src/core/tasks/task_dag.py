import asyncio
import logging
import uuid
from collections import OrderedDict
from typing import (
    Optional,
    List,
    TYPE_CHECKING,
    Mapping,
    Any,
    Self,
    cast,
    Type,
    Dict,
)

from pydantic import BaseModel, Field, ConfigDict, create_model

from core.callbacks.types import EventSenderObject, EventSender
from core.managers.async_event_manager import AsyncEventManager
from core.tasks.graph_element_with_parameters import GraphElementWithParameters
from core.tasks.task_data import TaskDataContract
from core.tasks.task_node import TaskNode
from core.tasks.task_path import TaskPath
from core.tasks.types import JSONParam, Status, ProcessMode, TaskEdgeKind
from misc.functions import extract_dag_id

if TYPE_CHECKING:
    from core.tasks.task import Task
    from core.context.context import Context
    from core.tasks.task_node import TaskEdge
    import pydot

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TaskDAG(GraphElementWithParameters, EventSenderObject):
    CURRENT: List["TaskDAG"] = []

    @staticmethod
    def parameters_factory() -> Type[BaseModel]:
        import enum
        from core.context.global_context import GlobalContext

        global_context = GlobalContext.get_instance()

        enum_values: Dict[str, str] = (
            {k: k for k in global_context.celery_workers}
            if global_context.celery
            else {}
        )
        dynamic_worker_tag_enum = enum.Enum("RequiredWorkerTag", enum_values)

        class Parameters(BaseModel):
            model_config = ConfigDict(extra="ignore")
            required_worker_tag: Optional[dynamic_worker_tag_enum | str] = None
            tags: List[str] = Field(default_factory=list)

        return Parameters

    def __init__(self, **kwargs) -> None:
        self._parameters = TaskDAG.parameters_factory().model_validate(kwargs)

        self._original_id = kwargs.pop("original_id", None)

        if "id" in kwargs and "label" not in kwargs:
            kwargs["label"] = kwargs["id"].replace("_", " ").title()

        self._variant = kwargs.pop("variant", None)
        self._job_id = kwargs.pop("job_id", None)
        super().__init__(**kwargs)
        self.task_node_map: dict[str, TaskNode] = OrderedDict()

        self._result_event_manager = AsyncEventManager()

        self._dag_paths: Optional[list[TaskPath]] = None
        if not self._original_id:
            self._original_id = self.id

        self._progress: Optional[float] = None
        self._task_group: Optional[asyncio.TaskGroup] = None
        self._edge_lock_map: Dict[str, asyncio.Lock] = {}
        self._edge_lock_map_lock = asyncio.Lock()

    @property
    def params(self) -> Mapping[str, Any]:
        return self._params_for_dag_and_key(self.id, "__dag__")

    def merge_params_input_models(self) -> Optional[Type[BaseModel]]:
        if not hasattr(self.__class__, "Parameters"):
            if hasattr(self.__class__, "parameters_factory"):
                class_param = getattr(self, "parameters_factory")()
            else:
                return None
        else:
            class_param = getattr(self.__class__, "Parameters")

        param_fields = class_param.model_fields

        param_values = self._params

        final_fields: Dict[str, Any] = {}
        for key, value in param_fields.items():
            if key not in param_values:
                final_fields[key] = (value.annotation, value)

        return create_model("RequiredParams", **final_fields)

    async def __acquire_edge_lock(self, from_task: "Task", to_task: "Task") -> None:
        lock_key = f"{from_task.id}::{to_task.id}"
        async with self._edge_lock_map_lock:
            edge_lock = self._edge_lock_map.get(lock_key)
            if edge_lock is None:
                edge_lock = asyncio.Lock()
            self._edge_lock_map[lock_key] = edge_lock
        await edge_lock.acquire()

    async def __release_edge_lock(self, from_task: "Task", to_task: "Task") -> None:
        lock_key = f"{from_task.id}::{to_task.id}"

        async with self._edge_lock_map_lock:
            edge_lock = self._edge_lock_map.get(lock_key)
            if edge_lock is not None:
                edge_lock.release()

    def serialize(self) -> Mapping[str, Any]:
        return {
            "_meta": {
                "id": self.id,
                "module": self.__class__.__module__,
                "class": self.__class__.__name__,
            },
            "task_nodes": [
                task_node.serialize() for task_node in self.task_node_map.values()
            ],
        }

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> "TaskDAG":
        meta_data = data["_meta"]
        meta_id = meta_data["id"]

        task_nodes_data = data["task_nodes"]

        work_dag = cls(id=meta_id)

        with work_dag:
            task_nodes = [TaskNode.deserialize(tn) for tn in task_nodes_data]

            new_task_node_map = OrderedDict({node.task.id: node for node in task_nodes})
            work_dag.task_node_map = new_task_node_map

        return work_dag

    def as_json(self) -> "JSONParam":
        ui_elements = []

        edges: List["TaskEdge"] = []
        for node in self.task_node_map.values():
            task = node.task

            ui_elements += task.get_field_ui()
            edges.extend(node.sub_nodes)

        json_dict = {
            **super().as_json(),
            "ui": ui_elements,
            "requiredWorkerTag": self.required_worker_tag,
        }

        from core.context.global_context import GlobalContext

        dag_manager = GlobalContext.get_instance().dag_manager
        if dag_manager.has_memory(self.id):
            memory = dag_manager.get_memory(self.id)

            json_dict["run"] = {
                "start": memory.start_date_iso,
                "end": memory.end_date_iso,
            }

        return json_dict

    def set_task_group(self, tg: Optional[asyncio.TaskGroup]) -> None:
        self._task_group = tg

    @property
    def event_source(self) -> EventSender:
        return EventSender("dag", self._original_id)

    @property
    def original_id(self) -> str:
        return self._original_id

    @property
    def job_id(self) -> str:
        return self._job_id

    @property
    def variant(self) -> Optional[str]:
        return self._variant

    @property
    def variant_id(self) -> str:
        dag_name, variant, _ = extract_dag_id(self.id)

        if variant != "_default_":
            return f"{dag_name}[{variant}]"

        return dag_name

    @property
    def required_worker_tag(self) -> Optional[str]:
        return self.params.get("required_worker_tag")

    def tasks_list(self) -> List[Dict[str, Any]]:
        return [node.task.as_json() for node in self.task_node_map.values()]

    @classmethod
    def get_dag(cls) -> Optional["TaskDAG"]:
        return cls.CURRENT[-1] if len(cls.CURRENT) else None

    # MARK: context manager
    def __enter__(self) -> Self:
        """Handler for context manager entry

        Returns:
            Self: the current instance
        """

        self.__class__.CURRENT.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Handler for context manager exit

        Args:
            exc_type: optional exception type
            exc_val: optional exception value
            exc_tb: optional exception traceback
        """
        self.__class__.CURRENT.pop()
        from core.context.global_context import GlobalContext

        GlobalContext.get_instance().register_dag(self)

    def clone(self, new_id: Optional[str] = None) -> "TaskDAG":
        """Helper method to clone a DAG

        Args:
            new_id (optional(str)): optional identifier for the cloned Dag

        Returns:
            TaskDAG: a new dag instance
        """
        final_id = new_id if new_id else self.id + ":" + str(uuid.uuid4())

        required_worker_tag = self.required_worker_tag

        _, variant, job_id = extract_dag_id(final_id)

        with TaskDAG(
            id=final_id,
            label=self.label,
            parent_id=self.id,
            job_id=job_id,
            variant=variant,
            required_worker_tag=required_worker_tag,
        ) as new_dag:
            for task_id, task_node in self.task_node_map.items():
                new_dag.task_node_map[task_id] = task_node.clone(
                    task_id=task_node.task.id, dag_id=final_id
                )

        return new_dag

    def get_root_tasks(self) -> List["Task"]:
        """Helper method to get root tasks

        Returns:
            List["Task"]: root tasks
        """

        root_task_nodes = (
            node for node in self.task_node_map.values() if not node.parent_nodes
        )

        return [node.task for node in root_task_nodes]

    def get_leaf_tasks(self) -> List["Task"]:
        """Helper method to get leaf tasks

        Returns:
            List["Task"]: leaf tasks
        """
        leaf_task_nodes = (
            node for node in self.task_node_map.values() if not node.sub_nodes
        )

        return [node.task for node in leaf_task_nodes]

    def add_child_task(
        self,
        parent_task: "Task",
        child_task: "Task",
        edge_type: "TaskEdgeKind" = TaskEdgeKind.DEFAULT,
    ) -> None:
        """Helper method to add a downstream relationship between two tasks

        Args:
            parent_task: the parent task
            child_task: the child/downstream task
            edge_type: the edge type, defaults to TaskEdgeKind.DEFAULT

        """
        parent_node: TaskNode = self.task_node_map[parent_task.id]

        if child_task.id not in self.task_node_map:
            child_node = TaskNode(self._id, child_task)
            self.task_node_map[child_task.id] = child_node
        else:
            child_node = self.task_node_map[child_task.id]

        parent_node.add_sub_node(child_node.task.id, edge_type=edge_type)

        child_node.add_parent_node(parent_node.task.id, edge_type=edge_type)

    def remove_parent_task(self, task_id: str, parent_task: "Task"):
        """Remove an edge between a task and a parent task

        Args:
            task_id: id of the child task
            parent_task: the parent task object
        """

        child_node: TaskNode = self.task_node_map[task_id]

        child_node.parent_nodes = [
            parent_edge
            for parent_edge in child_node.parent_nodes
            if parent_edge.from_id != parent_task.id
        ]

        parent_node: TaskNode = self.task_node_map[parent_task.id]

        parent_node.sub_nodes = [
            sub_node for sub_node in parent_node.sub_nodes if sub_node.to_id != task_id
        ]

    def register_task(self, task: "Task"):
        """Helper method to register a task as a task node

        Args:
            task: task object
        """
        task_node = TaskNode(self._id, task)
        self.task_node_map[task.id] = task_node

    def swap_task(self, task: "Task"):
        """Helper method to replace a task by another one

        Args:
            task: the new task object
        """
        task_node = self.task_node_map[task.id]
        task_node.task = task

    async def dag_did_finish(self):
        await self._result_event_manager.async_clear()

    @property
    def task_group(self) -> asyncio.TaskGroup:
        tg = self._task_group
        if not tg:
            raise ValueError("None taskgroup")
        return tg

    async def _lock_edges_after(
        self, task: "Task", for_mode=TaskEdgeKind.DEFAULT, release=False
    ) -> List["Task"]:
        task_node = self.task_node_map.get(task.id)

        if task_node is None:
            return []

        task_ids = task.tasks_after(task_node, for_mode=for_mode)

        tasks = [self.task_node_map[task_id].task for task_id in task_ids]

        for task_after in tasks:
            await self.__acquire_edge_lock(task, task_after)

        if release:
            for task_after in tasks:
                await self.__release_edge_lock(task, task_after)

        return tasks

    async def _lock_tasks_after(
        self, task: "Task", for_mode=TaskEdgeKind.DEFAULT, release: bool = False
    ) -> List["Task"]:
        task_node = self.task_node_map.get(task.id)

        if task_node is None:
            return []

        task_ids = task.tasks_after(task_node, for_mode=for_mode)

        tasks = [self.task_node_map[task_id].task for task_id in task_ids]

        for task_after in tasks:
            await task_after.get_lock()

        if release:
            for task_after in tasks:
                task_after.release_lock()

        return tasks

    async def task_did_finish(
        self,
        context,
        task: "Task",
        data_output: Mapping[str, Any],
        edge_kind: TaskEdgeKind = TaskEdgeKind.DEFAULT,
    ):
        tasks = await self._lock_edges_after(task, for_mode=edge_kind)

        value = data_output if data_output else {}
        await self._result_event_manager.async_value_received(task.id, value)

        for task_after in tasks:
            if task_after.status == Status.WAITING:
                continue
                # it is already waiting

            await task_after.set_status(context, Status.WAITING)

            self.task_group.create_task(
                self.schedule_task(context, task_after, data_output)
            )

    async def get_task_result(self, task_id: str) -> JSONParam:
        result = await self._result_event_manager.value(task_id)

        return cast(JSONParam, result)

    async def schedule_task(
        self,
        context: "Context",
        task: "Task",
        data_input: Optional[Mapping[str, Any]] = None,
    ):

        data_input = data_input if data_input else {}

        task_node: TaskNode = self.task_node_map[task.id]

        if task_node.parent_nodes:
            tasks = [
                self.task_group.create_task(self.get_task_result(parent_edge.from_id))
                for parent_edge in task_node.parent_nodes
            ]

            await asyncio.gather(*tasks)

            results = [item.result() for item in tasks]

            data_input = task_node.task.__class__.merge_data_in(data_input, *results)

        await task.set_status(context, Status.RUNNING)

        mode = task.process_mode

        if mode == ProcessMode.NORMAL:
            try:
                data_output = await task.process(context, data_input)
                if not isinstance(data_output, Mapping):
                    raise ValueError("data_output must be a mapping")
                await self.task_did_finish(context, task, data_output)

            except Exception as e:
                logger.exception("Exception during task %s processing %s", task.id, e)
                await task.set_status(context, Status.ERROR, error=e)

        elif mode == ProcessMode.GENERATOR:
            loop_start_data_input = await task.generator_process_before(
                context, data_input
            )

            await self.task_did_finish(
                context,
                task,
                loop_start_data_input,
                edge_kind=TaskEdgeKind.LOOP_START,
            )

            # we ensure all tasks launched as part of LOOP_START are finished at that point
            await self._lock_edges_after(
                task, for_mode=TaskEdgeKind.LOOP_START, release=True
            )

            data_output_iter = await task.generator_process(context, data_input)

            async for data_output_value in data_output_iter:
                await self.task_did_finish(
                    context, task, data_output_value, edge_kind=TaskEdgeKind.DEFAULT
                )

            # we ensure all tasks launched as part of LOOP are finished at that point
            await self._lock_edges_after(
                task, for_mode=TaskEdgeKind.DEFAULT, release=True
            )

            loop_start_data_input = await task.generator_process_after(
                context, data_input
            )

            await self.task_did_finish(
                context,
                task,
                loop_start_data_input,
                edge_kind=TaskEdgeKind.LOOP_END,
            )

        await task.set_status(context, Status.FINISHED)

        if task_node.parent_nodes:

            tasks_before = [
                self.task_node_map[parent_edge.from_id].task
                for parent_edge in task_node.parent_nodes
            ]
            for task_before in tasks_before:
                await self.__release_edge_lock(task_before, task)

    def as_graph(self) -> "pydot.Dot":
        import pydot

        graph = pydot.Dot("dag", graph_type="digraph", rankdir="LR")

        for task_node in self.task_node_map.values():
            task_node.add_to_graph(graph)

        return graph

    def _process_dag_paths_2(self):
        if self._dag_paths is not None:
            return self._dag_paths

        self._dag_paths = []

        for task_node in self.task_node_map.values():
            if task_node.sub_nodes:
                continue

            self._dag_paths.append(TaskPath(task_node.task.id))

        work_paths = self._dag_paths.copy()
        while True:
            new_path = []
            for work_path in work_paths:
                paths_iter = work_path.process_first_node(self)
                temp_path_list = []
                for path in paths_iter:
                    temp_path_list.append(path)
                    new_path.append(path)

                for new_element in temp_path_list[:-1]:
                    self._dag_paths.append(new_element)

            work_paths = new_path

            if not new_path:
                break

        return self._dag_paths

    def _process_dag_paths(self):
        if self._dag_paths is not None:
            return self._dag_paths

        self._dag_paths = []
        for task_node in self.task_node_map.values():
            if task_node.parent_nodes:
                continue

            self._dag_paths.append(TaskPath(task_node.task.id))

        work_paths = self._dag_paths.copy()
        while True:
            new_path = []
            for work_path in work_paths:
                paths_iter = work_path.process_last_node(self)
                temp_path_list = []
                for path in paths_iter:
                    temp_path_list.append(path)
                    new_path.append(path)

                for new_element in temp_path_list[:-1]:
                    self._dag_paths.append(new_element)

            if not new_path:
                break

        return self._dag_paths

    def required_params(self) -> Mapping[str, Type[BaseModel]]:
        params_dict = {}

        for task_id, task_node in self.task_node_map.items():
            task = task_node.task

            task_required_params = task.required_params()

            if task_required_params:
                params_dict[task_id] = task_required_params

        return params_dict

    def get_required_inputs(self) -> TaskDataContract:
        leaf_tasks = self.get_leaf_tasks()

        full_contract = TaskDataContract()
        for task in leaf_tasks:
            full_contract.add_all(self._required_inputs_for_task(task))

        return full_contract

    def _provided_outputs_for_task(self, task: "Task") -> TaskDataContract:
        parent_task_nodes = self.task_node_map[task.id].parent_nodes

        if not parent_task_nodes:
            return task.provided_outputs()

        parents_task_data_contract = TaskDataContract()
        for parent_node in parent_task_nodes:
            parent_task = self.task_node_map[parent_node.from_id].task
            parents_task_data_contract.add_all(
                self._provided_outputs_for_task(parent_task)
            )

        return task.provided_outputs(parents_task_data_contract)

    def _required_inputs_for_task(self, task: "Task") -> TaskDataContract:

        contract = task.required_inputs()

        parent_task_nodes = self.task_node_map[task.id].parent_nodes

        for parent_node in parent_task_nodes:
            parent_task = self.task_node_map[parent_node.from_id].task

            provided_output_for_parent_tasks = self._provided_outputs_for_task(
                parent_task
            )
            contract.subtract_all(provided_output_for_parent_tasks)

            required_input_for_task = self._required_inputs_for_task(parent_task)

            contract.add_all(required_input_for_task)

        return contract

    def get_required_inputs_old(self) -> TaskDataContract:
        contract = TaskDataContract()

        paths = self._process_dag_paths_2()

        for path in paths:
            path_required_input = path.get_required_inputs(self)

            contract.add_all(path_required_input)

        return contract

    async def set_progress(self, context: "Context", value: float) -> None:

        await context.event(self, "progress", {"progress": value})

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
        from core.tasks.types import Status

        if value == Status.RUNNING:
            self._edge_lock_map.clear()
            self._edge_lock_map_lock = asyncio.Lock()

        await context.event(
            self,
            "status",
            {"status": value, "error": error},
        )

        super().set_status(context, value, error=error, **kwargs)

    async def reset_task_status(self, context: "Context"):
        for node in self.task_node_map.values():
            await node.task.set_status(context, Status.IDLE, send_value=False)
