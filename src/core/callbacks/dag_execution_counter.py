from typing import Dict, Optional, TYPE_CHECKING, Any, List, Mapping, Tuple, cast

import flask

from core.callbacks.callback_handler import CallbackHandler
from core.callbacks.types import EventSenderParam
from core.tasks.types import Status

if TYPE_CHECKING:
    from core.context.context import Context

StatusTimestamp = Tuple[Status, float]
StatusTimeStampList = List[StatusTimestamp]
StatusTimeStampListMap = Dict[str, StatusTimeStampList]


class DAGExecutionCounter(CallbackHandler):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._running_count = 0
        self._dag_status: Dict[str, Status] = {}

    def is_event_handled(
        self, context: "Context", sender: EventSenderParam, event=False
    ) -> bool:
        from core.tasks.task_dag import TaskDAG

        return (isinstance(sender, TaskDAG) and event == "status") or (
            sender == "global" and event == "subscribe_running_dag_count"
        )

    async def on_handled_event(
        self,
        context: "Context",
        sender: EventSenderParam,
        event: str,
        payload: Optional[Mapping[str, Any]],
        raw_payload=False,
    ) -> bool:

        print(f"{sender} {event}")
        from core.context.global_context import GlobalContext

        global_context = context.cast_as(GlobalContext)
        websocket_manager = global_context.websocket_manager if global_context else None

        emit_to = "runningDagRoom"

        if (
            sender == "global"
            and event == "subscribe_running_dag_count"
            and websocket_manager
        ):
            emit_to = getattr(flask.request, "sid")

        elif event == "status":
            from core.tasks.task_dag import TaskDAG

            if not isinstance(payload, dict):
                raise ValueError(
                    "Bad payload, dict expected got {}".format(type(payload))
                )

            task_dag = cast(TaskDAG, sender)

            status = cast(Status, payload.get("status"))
            previous_status = self._dag_status.get(task_dag.id)
            self._dag_status[task_dag.id] = status

            if status == Status.RUNNING and previous_status != Status.RUNNING:
                self._running_count += 1
            elif status != Status.RUNNING and previous_status == Status.RUNNING:
                self._running_count -= 1
            else:
                return False

        if not websocket_manager:
            return False

        websocket_manager.websocket.emit(
            "runningDagCount", self._running_count, to=emit_to
        )

        return False
