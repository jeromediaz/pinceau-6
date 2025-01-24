from typing import Optional, Mapping, Any, TYPE_CHECKING

from conf import Config
from conf.config import RunMode
from core.callbacks.callback_handler import CallbackHandler
from core.callbacks.types import EventSenderParam

if TYPE_CHECKING:
    from core.context.context import Context


class WebsocketCallbackHandler(CallbackHandler):
    def __init__(self, socket, to, **kwargs):
        super().__init__(**kwargs)
        self._socket = socket
        self._to = to
        conf = Config()
        self._run_mode = conf.run_mode

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

    def is_event_handled(
        self, context: "Context", sender: EventSenderParam, event=False
    ) -> bool:

        return isinstance(sender, str)

    async def on_handled_event(
        self,
        context: "Context",
        sender: EventSenderParam,
        event: str,
        payload: Optional[Mapping[str, Any]],
        raw_payload=False,
    ) -> bool:
        final_sender = str(sender)

        data = (
            {"sender": final_sender, "payload": payload if payload else {}}
            if not raw_payload
            else payload
        )
        if self._run_mode == RunMode.WORKER:
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

        try:
            if event and isinstance(event, str):
                self._socket.emit(event, data, to=self._to)
            else:
                self._socket.send(data, to=self._to)
        except Exception:
            pass

        return False
