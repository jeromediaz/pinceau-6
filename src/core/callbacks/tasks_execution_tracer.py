import time
from typing import Dict, Optional, TYPE_CHECKING, Any, List, Mapping, Tuple, Union, cast

from core.callbacks.callback_handler import CallbackHandler
from core.callbacks.types import EventSenderParam
from core.tasks.task import Task
from core.tasks.types import Status

if TYPE_CHECKING:
    from core.context.context import Context


StatusTimestamp = Tuple[Status, float]
StatusTimeStampList = List[StatusTimestamp]
StatusTimeStampListMap = Dict[str, StatusTimeStampList]


class TasksExecutionTracer(CallbackHandler):

    def __init__(self, dag_id: str):
        super().__init__()
        self._dag_id = dag_id
        self._task_traces: StatusTimeStampListMap = {}

    def serialize(self) -> Mapping[str, Any]:
        return {**super().serialize(), "dag_id": self._dag_id}

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> Any:
        dag_id = data["dag_id"]

        return cls(dag_id)

    def is_event_handled(
        self, context: "Context", sender: EventSenderParam, event=False
    ) -> bool:
        from core.tasks.task import Task

        return isinstance(sender, Task) and event == "status"

    async def on_handled_event(
        self,
        context: "Context",
        sender: EventSenderParam,
        event: str,
        payload: Optional[Mapping[str, Any]],
        raw_payload=False,
    ) -> bool:
        sender_event_id = cast(Task, sender).full_id

        if payload:
            status = cast(Status, payload.get("status"))

            task_trace = self._task_traces.setdefault(sender_event_id, [])
            task_trace.append((status, time.time()))

        return False

    def task_start_duration(self, task: Union["Task", str]):
        task_id = task.full_id if isinstance(task, Task) else task
        task_trace = self._task_traces.setdefault(task_id, [])
        print(task_trace)

    def task_status_start_duration(
        self, task: Union["Task", str], status: Status
    ) -> List[Tuple[float, float]]:

        task_id = task.full_id if isinstance(task, Task) else task

        task_trace = self._task_traces.setdefault(task_id, [])

        previous_ts: float = 0.0

        results = []

        for trace in task_trace:
            trace_status, start_ts = trace

            if previous_ts:
                results.append((previous_ts, start_ts - previous_ts))
                previous_ts = 0
            if trace_status == status:
                previous_ts = start_ts

        if previous_ts:
            results.append((previous_ts, -1))

        return results

    @property
    def known_tasks(self) -> int:
        return len(self._task_traces)
