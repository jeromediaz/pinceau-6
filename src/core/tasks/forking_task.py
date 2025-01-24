from math import ceil
from typing import Optional, TYPE_CHECKING, Self, Mapping, Any

from core.tasks.task import Task
from core.tasks.types import TaskEdgeKind

if TYPE_CHECKING:
    from core.context.context import Context


class ForkingTask(Task):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._fork_index = kwargs.get("fork_index", -1)
        self._fork_input_key = kwargs["fork_input_key"]
        self._fork_chunk_max_size = kwargs.get("chunk_max_size", 1)

    def clone(self, fork_index: Optional[int] = None, **kwargs) -> Self:
        final_index = fork_index if fork_index is not None else self._fork_index
        copy_params = dict(self.params)

        if fork_index is not None:
            copy_params["id"] = f"{self.id}_{fork_index}"
            copy_params["label"] = f"{self.label} - {fork_index}"

        return self.__class__(
            fork_index=final_index,
            **copy_params,
            **kwargs,
        )

    async def process(
        self, context: "Context", data_in: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        work_list = data_in[self._fork_input_key]

        if self._fork_index != -1:
            data_in = {**data_in}
            start_index = self._fork_index * self._fork_chunk_max_size
            end_index = start_index + self._fork_chunk_max_size
            data_in[self._fork_input_key] = work_list[start_index:end_index]

            return await self._process(context, data_in)

        if len(work_list) <= self._fork_chunk_max_size:
            return await self._process(context, data_in)

        chunk_count = ceil(float(len(work_list)) / float(self._fork_chunk_max_size))

        work_dag = self.dag()
        self_node = self.node

        if self_node is None or work_dag is None:
            raise ValueError("Cannot be used outside a DAG")

        next_node_ids = self_node.sub_nodes.copy()
        next_node_tasks = list(
            map(
                lambda task_edge: work_dag.task_node_map[task_edge.to_id].task,
                next_node_ids,
            )
        )

        for next_node_id in next_node_ids:
            work_dag.remove_parent_task(next_node_id, self)

        # let the fork begin!
        for chunk_index in range(0, chunk_count):
            sub_task = self.clone(chunk_index, dag=work_dag)

            work_dag.add_child_task(self, sub_task, edge_type=TaskEdgeKind.DEFAULT)

            for next_task in next_node_tasks:
                work_dag.add_child_task(
                    sub_task, next_task, edge_type=TaskEdgeKind.DEFAULT
                )

        return {**data_in}
