from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING, Mapping, Any

from core.callbacks.callback import Callback
from core.callbacks.types import EventSenderParam

if TYPE_CHECKING:
    from core.context.context import Context


class CallbackHandler(Callback, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def on_event(
        self,
        context: "Context",
        sender: EventSenderParam,
        event: str,
        payload: Optional[Mapping[str, Any]],
        raw_payload=False,
    ) -> bool:
        if not self.is_event_handled(context, sender, event):
            return False  # do not stop propagation

        return await self.on_handled_event(context, sender, event, payload, raw_payload)

    @abstractmethod
    async def on_handled_event(
        self,
        context: "Context",
        sender: EventSenderParam,
        event: str,
        payload: Optional[Mapping[str, Any]],
        raw_payload=False,
    ) -> bool:
        pass
