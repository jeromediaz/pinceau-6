from threading import Lock
from typing import Optional, TYPE_CHECKING, Mapping, Any

from conf import Config
from conf.config import RunMode
from core.callbacks.callback_handler import CallbackHandler
from core.callbacks.types import EventSenderParam

if TYPE_CHECKING:
    from core.context.context import Context


class DagWebsocketCallbackHandler(CallbackHandler):

    def __init__(self, socket, to, **kwargs):
        super().__init__(**kwargs)

        self._socket = socket
        self._to = to
        conf = Config()
        self._run_mode = conf.run_mode
        self._lock = Lock()

    def serialize(self) -> Mapping[str, Any]:
        return {**super().serialize(), "to": self._to}

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> Any:
        conf = Config()
        from core.context.global_context import GlobalContext

        global_context = GlobalContext.get_instance()
        if conf.run_mode == RunMode.WORKER:
            socket = global_context.websocket_client

            return cls(socket, data["to"])
        else:
            websocket_manager = global_context.websocket_manager
            socket = websocket_manager.websocket if websocket_manager else None

            return cls(socket, data["to"])

    async def on_handled_event(
        self,
        context: "Context",
        sender: EventSenderParam,
        event: str,
        payload: Optional[Mapping[str, Any]],
        raw_payload=False,
    ) -> bool:
        emit = event in {"ws", "ws_dag_room"}
        work_event = ""

        to = None if event == "ws" else self._to

        if not emit:
            return False

        data = (
            {"sender": str(sender), "payload": payload if payload else {}}
            if not raw_payload
            else payload
        )

        if self._run_mode == RunMode.WORKER:
            with self._lock:
                try:
                    relay_data = {
                        "relay": data,
                        "to": self._to,
                    }
                    if event and isinstance(event, str):
                        relay_data["event"] = event

                    self._socket.emit("worker_relay", relay_data)
                except AssertionError:
                    pass
                return False

        with self._lock:
            try:
                if work_event and isinstance(work_event, str):
                    self._socket.emit(work_event, data, to=to)
                else:
                    self._socket.send(data, to=to)
            except Exception as e:
                print(e)

        # DATA was handled, stop event propagation
        return True
