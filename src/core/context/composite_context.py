from typing import List, Optional, Any, Type, Self, Mapping

from core.callbacks.types import EventSenderParam
from core.context.context import Context, CastContext
from core.context.local_context import LocalContext
from core.utils import deserialize_instance


class CompositeContext(Context):
    def __init__(self, *children, **kwargs) -> None:
        super().__init__(**kwargs)
        self._children: List[Context] = list(children)

    def serialize(self) -> Mapping[str, Any]:
        serialized_value = {
            **super().serialize(),
            "children": [child.serialize() for child in self._children],
        }

        return serialized_value

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> Any:
        new_composite_context = cls()

        for child in data["children"]:
            new_composite_context.add_layer(deserialize_instance(child))

        return new_composite_context

    def __str__(self):
        str_value = self.__class__.__name__

        children_context_names = list(
            map(lambda context: context.__class__.__name__, self._children)
        )

        return f"{str_value}[{' > '.join(children_context_names[::-1])}]"

    async def on_handled_event(
        self,
        context: "Context",
        sender: EventSenderParam,
        event: str,
        payload: Optional[Mapping[str, Any]],
        raw_payload=False,
    ) -> bool:
        if await self._callback_manager.on_event(
            context, sender, event, payload, raw_payload
        ):
            # self callback manager stopped propagation
            return True

        for sub_context in self._children[::-1]:
            if await sub_context.on_event(context, sender, event, payload, raw_payload):
                return True

        return False

    def has(self, key: str) -> bool:
        return self._children[-1].has(key)

    def get(
        self, key: str, default: Optional[Any] = None, recursive: bool = True
    ) -> Any:
        if not recursive:
            return self._children[-1].get(key, default)

        for sub_context in self._children[::-1]:
            if sub_context.has(key):
                return sub_context.get(key)

        return default

    def set(self, key: str, value: Any):
        return self._children[-1].set(key, value)

    def update(self, key: str, value: Any) -> bool:
        for sub_context in self._children[::-1]:
            if sub_context.has(key):
                return sub_context.set(key, value)

        return False

    def add_layer(self, layer: Context) -> Self:
        self._children.append(layer)
        return self

    def create_local_context(self, callbacks=None) -> LocalContext:
        new_context = LocalContext(callbacks)
        self.add_layer(new_context)
        return new_context

    def __getattr__(self, item: str) -> Any:
        for sub_context in self._children[::-1]:
            if hasattr(sub_context, item):
                return getattr(sub_context, item)

        return None

    def cast_as(self, context_type: Type[CastContext]) -> CastContext:
        for sub_context in self._children[::-1]:
            if isinstance(sub_context, context_type):
                return sub_context

        raise ValueError(f"{self} can't be cast as {context_type.__name__}")
