from typing import Union, Optional, Sequence, TYPE_CHECKING, Mapping, Any, List

from core.callbacks.callback import Callback
from core.callbacks.types import EventSenderParam
from core.utils import deserialize_instance

if TYPE_CHECKING:
    from core.callbacks.callback_handler import CallbackHandler
    from core.context.context import Context


class CallbackManager(Callback):
    def __init__(self, handlers, **kwargs) -> None:
        super().__init__(**kwargs)
        self._handlers: List["CallbackHandler"] = list(handlers)

    def serialize(self) -> Mapping[str, Any]:
        serialize_value = {
            **super().serialize(),
            "handlers": [handler.serialize() for handler in self._handlers],
        }
        return serialize_value

    @classmethod
    def deserialize(cls, serialized: Mapping[str, Any]) -> "CallbackManager":
        handlers_data = serialized["handlers"]

        handlers = [
            deserialize_instance(handler_data) for handler_data in handlers_data
        ]

        return cls(handlers)

    async def on_event(
        self,
        context: "Context",
        sender: EventSenderParam,
        event: str,
        payload: Optional[dict],
        raw_payload=False,
    ) -> bool:
        if not self.is_event_handled(context, sender, event):
            return False  # do not stop propagation

        for handler in self._handlers:
            if await handler.on_event(context, sender, event, payload, raw_payload):
                return True  # stop propagation

        return False  # continue propagation

    @classmethod
    def from_list(
        cls, manager: Union["CallbackManager", Sequence["CallbackHandler"]]
    ) -> "CallbackManager":
        if isinstance(manager, cls):
            return manager

        else:
            return cls(manager)
