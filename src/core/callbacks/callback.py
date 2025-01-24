from abc import ABC, abstractmethod
from typing import Optional, Mapping, Any, TYPE_CHECKING

from core.callbacks.types import EventSenderParam

if TYPE_CHECKING:
    from core.context.context import Context


class Callback(ABC):
    def __init__(self, **kwargs):
        # empty implementation
        pass

    def serialize(self) -> Mapping[str, Any]:
        return {
            "_meta": {
                "module": self.__class__.__module__,
                "class": self.__class__.__name__,
            }
        }

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> Any:
        return cls()

    @abstractmethod
    async def on_event(
        self,
        context: "Context",
        sender: EventSenderParam,
        event: str,
        payload: Optional[dict],
    ) -> bool:
        pass

    def is_event_handled(
        self, context: "Context", sender: EventSenderParam, event=False
    ) -> bool:
        return True
