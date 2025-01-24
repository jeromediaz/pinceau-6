import copy
from typing import Any, TypeVar, Mapping
from typing import Optional

from core.callbacks.callback_manager import CallbackManager
from core.context.context import Context
from core.utils import deserialize_instance

CastContext = TypeVar("CastContext", bound="Context")


class LocalContext(Context):
    def __init__(self, callbacks=None, values: Optional[dict] = None, **kwargs):
        super().__init__(**kwargs)
        self._values = copy.deepcopy(values) if values else {}

        self._callback_manager = CallbackManager.from_list(
            callbacks if callbacks else []
        )

    def serialize(self) -> Mapping[str, Any]:
        return {
            **super().serialize(),
            "values": self._values,
            "callbacks": self._callback_manager.serialize(),
        }

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> Any:
        values = data["values"]
        callbacks = deserialize_instance(data["callbacks"])
        return cls(callbacks=callbacks, values=values)

    def has(self, key: str) -> bool:
        return key in self._values

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._values.get(key, default)

    def set(self, key: str, value: Any):
        self._values[key] = value

    def update(self, key: str, value: Any) -> bool:
        if self.has(key):
            self.set(key, value)
            return True

        return False
