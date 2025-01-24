from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence

from core.tasks.task import Task
from core.tasks.types import Status, TaskEdgeKind
from ui.ag_charts_field import AGChartsObject, AGChartsField

if TYPE_CHECKING:
    from core.context.context import Context
    from core.tasks.task_node import TaskNode


test_chart = AGChartsField(source="chart_data")
test_chart.title["text"] = "Loss"
test_chart.series.append(AGChartsObject(type="line", xKey="0", yKey="1", yName="test"))


class RoundRobinTask(Task):

    def __init__(self, **kwargs):
        kwargs.setdefault("is_passthrough", True)
        super().__init__(**kwargs)
        self._index = 0

    def tasks_after(
        self, node: "TaskNode", for_mode: TaskEdgeKind = TaskEdgeKind.DEFAULT
    ) -> Sequence[str]:
        if not node.sub_nodes:
            return []

        sub_nodes = node.usable_sub_nodes(for_mode=for_mode)

        if self._index >= len(sub_nodes):
            self._index = 0

        value = [sub_nodes[self._index].to_id]
        self._index += 1

        return value

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:

        return data_input

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
        if value == Status.IDLE:
            self._index = 0

        await super().set_status(
            context, value, send_value=send_value, error=error, **kwargs
        )
