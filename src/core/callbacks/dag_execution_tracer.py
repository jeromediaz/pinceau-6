from typing import Dict, Optional, TYPE_CHECKING, Any, List, Mapping, Tuple, cast

from core.callbacks.callback_handler import CallbackHandler
from core.callbacks.types import EventSenderParam
from core.tasks.types import Status

if TYPE_CHECKING:
    from core.context.context import Context
import time

StatusTimestamp = Tuple[Status, float]
StatusTimeStampList = List[StatusTimestamp]
StatusTimeStampListMap = Dict[str, StatusTimeStampList]


class DAGExecutionTracer(CallbackHandler):

    def __init__(self, dag_id: str, **kwargs):
        super().__init__()
        self._dag_id = dag_id
        self._dag_trace: StatusTimeStampList = []

    def serialize(self) -> Mapping[str, Any]:
        return {**super().serialize(), "dag_id": self._dag_id}

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> Any:
        dag_id = data["dag_id"]

        return cls(dag_id)

    def is_event_handled(
        self, context: "Context", sender: EventSenderParam, event=False
    ) -> bool:
        from core.tasks.task_dag import TaskDAG

        return isinstance(sender, TaskDAG) and event == "status"

    async def on_handled_event(
        self,
        context: "Context",
        sender: EventSenderParam,
        event: str,
        payload: Optional[Mapping[str, Any]],
        raw_payload=False,
    ) -> bool:
        if payload:
            status = cast(Status, payload.get("status"))
            self._dag_trace.append((status, time.time()))

        return False

    @property
    def last_status(self) -> Optional[Status]:
        if self._dag_trace:
            return self._dag_trace[-1][0]
        return None
