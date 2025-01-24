from typing import TYPE_CHECKING, Mapping, Any, Sequence, Optional, cast

from pydantic import BaseModel

from applications.chat.tasks import BaseChatTask
from core.context.chat_context import ChatContext
from core.tasks.types import TaskEdgeKind
from tasks.zero_shot_classification_task import ZeroShotClassificationTask

if TYPE_CHECKING:
    from core.tasks.task_dag import TaskDAG
    from core.tasks.task_node import TaskNode
    from core.context.context import Context


class ChatZeroShotBranchingTask(BaseChatTask):

    class OutputModel(BaseModel):
        classes: Sequence[str]

    class InputModel(BaseModel):
        chat_id: str
        message: str

    def __init__(self, model: str = "facebook/bart-large-mnli", **kwargs):
        super().__init__(**kwargs)
        self._model = model
        self._tasks_after: list[str] = []

    def clone(self, **kwargs) -> "BaseChatTask":
        return self.__class__(self._model, **self.params, **kwargs)

    def tasks_after(
        self, node: "TaskNode", for_mode: TaskEdgeKind = TaskEdgeKind.DEFAULT
    ) -> Sequence[str]:
        return self._tasks_after

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:

        chat_context = context.cast_as(ChatContext)

        data_input_object = self.input_object(data_input)

        sub_task = ZeroShotClassificationTask(dag=self.dag(), _register_task=False)

        task_description_mapping: dict[str, str] = dict()
        classes: list[str] = list()

        dag: Optional["TaskDAG"] = self.dag()
        node: Optional["TaskNode"] = self.node

        if node is None or dag is None:
            raise ValueError("This task cannot be called outside a DAG")

        for edge in node.sub_nodes:
            task = dag.task_node_map[edge.to_id].task
            classes.append(task.description)
            task_description_mapping[task.description] = task.id

        sub_task_result = cast(
            Mapping[str, Any],
            await sub_task.process(
                context, {"query": data_input_object.message, "classes": classes}
            ),
        )

        next_task_id = task_description_mapping[sub_task_result["labels"][0]]
        self._tasks_after = [next_task_id]

        await chat_context.add_system_message(
            context, f"Using task {next_task_id}", from_user="agent:system"
        )

        return {**data_input, "classes": classes}
