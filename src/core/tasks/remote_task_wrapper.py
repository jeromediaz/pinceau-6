import json
from enum import Enum
from typing import Mapping, Any, Optional, TYPE_CHECKING, Sequence

from pydantic import BaseModel

from core.context.global_context import GlobalContext
from core.tasks.task import Task
from core.tasks.task_data import TaskDataContract
from core.tasks.types import ProcessMode, TaskData, TaskEdgeKind

if TYPE_CHECKING:
    from core.context.context import Context
    from core.tasks.task_node import TaskNode


class RemoteTaskWrapper(Task):

    def __init__(self, task: Task, worker_tag: str = "celery", **kwargs):
        self._wrapped_task = task
        self._worker_tag = worker_tag
        kwargs["id"] = task.id
        super().__init__(**kwargs)

        if task.process_mode != ProcessMode.NORMAL:
            raise ValueError("Wrapped task must implement _process")

    def clone(self, **kwargs) -> "Task":

        other_params = {}
        if "id" in kwargs and "id" not in self.params:
            other_params["id"] = kwargs.pop("id")

        return self.__class__(
            task=self._wrapped_task.clone(
                id=self._wrapped_task.id, _register_task=False
            ),
            is_passthrough=self.is_passthrough,
            **self.params,
            **other_params
        )

    def process_input_model(self):
        return self._wrapped_task.process_input_model()

    def input_object(self, data: Mapping[str, Any]):
        return self._wrapped_task.input_object(data)

    def required_inputs(self) -> TaskDataContract:
        return self._wrapped_task.required_inputs()

    def provided_outputs(
        self, parent_task_output: Optional[TaskDataContract] = None
    ) -> TaskDataContract:
        return self._wrapped_task.provided_outputs(parent_task_output)

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:

        global_context = context.cast_as(GlobalContext)
        if not global_context.celery:
            raise RuntimeError("Celery is not initialized")

        class PydanticEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, BaseModel):
                    return obj.model_dump()
                if isinstance(obj, Enum):
                    return obj.value
                # Let the base class default method raise the TypeError
                return super().default(obj)

        try:
            print("before sending task to celery")
            result = global_context.celery.send_task(
                "worker.run_task",
                [
                    self._wrapped_task.serialize(),
                    json.loads(json.dumps(context.serialize(), cls=PydanticEncoder)),
                    json.loads(json.dumps(data_in, cls=PydanticEncoder)),
                ],
                queue=self._worker_tag,
            )
            print("celery task sent!")
        except Exception as e:
            print(e)

        final_data = {**data_in, **result.get()}

        return final_data

    def tasks_after(
        self, node: "TaskNode", for_mode: TaskEdgeKind = TaskEdgeKind.DEFAULT
    ) -> Sequence[str]:
        return self._wrapped_task.tasks_after(node, for_mode=for_mode)
