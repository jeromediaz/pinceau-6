from typing import TYPE_CHECKING, Mapping, Any

from core.context.global_context import GlobalContext
from core.tasks.task import Task
from core.tasks.task_dag import TaskDAG
from core.tasks.types import TaskData
from core.utils import deserialize_instance

if TYPE_CHECKING:
    from core.tasks.task_data import TaskDataContract
    from core.context.context import Context
    from core.tasks.task_dag import TaskDAG


class SerializedDAGProcessingTask(Task):

    def __init__(self, dag: "TaskDAG", **kwargs) -> None:
        super().__init__(**kwargs)
        self._wrapped_dag = dag

    def clone(self, **kwargs) -> "Task":
        params_copy = {**self.params}

        return self.__class__(
            dag=self._wrapped_dag,
            is_passthrough=self.is_passthrough,
            **params_copy,
        )

    def serialize(self) -> Mapping[str, Any]:
        return {
            **super().serialize(),
            "dag": self._wrapped_dag.serialize(),
        }

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> "Task":
        dag_data = data["dag"]
        meta_data = data["_meta"]
        task_id = meta_data["id"]
        params = data["_params"]

        dag_object = deserialize_instance(dag_data)

        return cls(dag=dag_object, id=task_id, **params)

    def required_inputs(self) -> "TaskDataContract":
        return self._wrapped_dag.get_required_inputs()

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        print("_______________________")

        global_context = context.cast_as(GlobalContext)

        await global_context.run_dag(self._wrapped_dag, data_in, context=context)
        return {}
