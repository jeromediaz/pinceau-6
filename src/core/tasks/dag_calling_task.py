from typing import TYPE_CHECKING

from core.context.global_context import GlobalContext
from core.tasks.task import Task
from core.tasks.types import TaskData

if TYPE_CHECKING:
    from core.tasks.task_data import TaskDataContract
    from core.context.context import Context


class DAGCallingTask(Task):

    def __init__(self, dag_id: str, **kwargs) -> None:
        super().__init__(**kwargs)

        self._dag_id = dag_id
        self._params["dag_id"] = dag_id

    def clone(self, **kwargs) -> "Task":
        params_copy = {**self.params}
        params_copy.pop("dag_id")
        params_copy.update(kwargs)

        other_params = {}
        if "id" in kwargs and "id" not in params_copy:
            other_params["id"] = kwargs.pop("id")

        return self.__class__(
            dag_id=self._dag_id,
            is_passthrough=self.is_passthrough,
            **params_copy,
            **other_params,
        )

    def required_inputs(self) -> "TaskDataContract":
        return (
            GlobalContext.get_instance().dag_manager[self._dag_id].get_required_inputs()
        )

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        print("_______________________")
        print(f"{self._dag_id=}")
        global_context = context.cast_as(GlobalContext)
        dag_manager = global_context.dag_manager

        if self._dag_id not in dag_manager:
            dag_id_parts = self._dag_id.split(":")
            if len(dag_id_parts) == 2:
                parent_id, child_id = dag_id_parts

                if parent_id in dag_manager:
                    dag_manager[parent_id].clone(self._dag_id)

        dag = global_context.dag_manager[self._dag_id]

        for key, task_node in dag.task_node_map.items():
            for task_edge in task_node.sub_nodes:
                print(f"    {str(task_edge)}")
                print(f"    params={task_node.task.params}")

        await global_context.run_dag(dag, data_in, context=context)
        return {}
