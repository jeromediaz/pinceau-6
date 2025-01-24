from typing import Any, TypeVar, Type, TYPE_CHECKING, Mapping
from typing import Optional

from core.callbacks.callback_handler import CallbackHandler
from core.callbacks.callback_manager import CallbackManager
from core.callbacks.types import EventSender, EventSenderObject, EventSenderParam
from core.utils import deserialize_instance

CastContext = TypeVar("CastContext", bound="Context")

if TYPE_CHECKING:
    from core.tasks.task import Task


class Context(CallbackHandler):
    def __init__(self, callbacks=None, **kwargs):
        super().__init__(**kwargs)

        self._callback_manager = CallbackManager.from_list(
            callbacks if callbacks else []
        )

    def serialize(self) -> Mapping[str, Any]:
        return {
            **super().serialize(),
            "_callback_manager": self._callback_manager.serialize(),
        }

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> Any:
        callback_manager = deserialize_instance(data["_callback_manager"])
        return cls(callbacks=callback_manager)

    async def event(
        self,
        sender: EventSenderParam,
        event: str,
        payload: Optional[Mapping[str, Any]] = None,
        raw_payload=False,
    ) -> bool:
        return await self.on_event(
            self, sender, event, payload, raw_payload=raw_payload
        )

    async def on_handled_event(
        self,
        context: "Context",
        sender: str | EventSender | EventSenderObject,
        event: str,
        payload: Optional[Mapping[str, Any]],
        raw_payload=False,
    ) -> bool:
        return await self._callback_manager.on_event(
            context, sender, event, payload, raw_payload
        )

    def has(self, key: str) -> bool:
        del key  # unused in default implementation
        return False

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        del key, default  # unused in default implementation
        return None

    def set(self, key: str, value: Any):
        del key, value  # unused in default implementation
        # default implementation does nothing
        pass

    def update(self, key: str, value: Any) -> bool:
        del key, value  # unused in default implementation
        # default implementation does nothing
        return False

    def cast_as(self, context_type: Type[CastContext]) -> CastContext:
        if not isinstance(self, context_type):
            raise ValueError(
                f"{self.__class__.__name__} can't be cast as {context_type}"
            )
        return self

    async def task_log(self, task: "Task", message: str):
        await self.on_event(
            self, task, "", {"log": {"task": task.full_id, "msg": message}}
        )
