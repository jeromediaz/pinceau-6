from typing import TYPE_CHECKING, Sequence, Mapping, Any, Optional, cast

from pydantic import BaseModel, Field

from core.tasks.task import Task
from core.tasks.types import TaskEdgeKind
from tasks.zero_shot_classification_task import ZeroShotClassificationTask

if TYPE_CHECKING:
    from core.tasks.task_dag import TaskDAG
    from core.tasks.task_node import TaskNode
    from core.context.context import Context


class ZeroShotBranchingTask(Task):
    class UI(BaseModel):
        result: str = Field(title="result")

    class InputModel(BaseModel):
        query: str

    class OutputModel(BaseModel):
        classification: dict

    def __init__(self, model: str = "facebook/bart-large-mnli", **kwargs):
        super().__init__(**kwargs)
        self._model = model
        self._tasks_after: list[str] = []

    def clone(self, **kwargs) -> "Task":
        return self.__class__(self._model, **self.params, **kwargs)

    def tasks_after(
        self, node: "TaskNode", for_mode: TaskEdgeKind = TaskEdgeKind.DEFAULT
    ) -> Sequence[str]:
        return self._tasks_after

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        sub_task = ZeroShotClassificationTask(dag=self.dag())

        task_description_mapping = dict()
        classes = list()

        dag: Optional["TaskDAG"] = self.dag()
        node: Optional["TaskNode"] = self.node

        if node is None or dag is None:
            raise ValueError("This task cannot be called outside a DAG")

        for edge in node.sub_nodes:
            task = dag.task_node_map[edge.to_id].task
            classes.append(task.description)
            task_description_mapping[task.description] = task.id

        work_input = {**data_input, "classes": classes}
        sub_task_result = cast(
            Mapping[str, Any], await sub_task.process(context, work_input)
        )

        next_task_id = task_description_mapping[sub_task_result["labels"][0]]
        self._tasks_after = [next_task_id]

        return {**work_input}
