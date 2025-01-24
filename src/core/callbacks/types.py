from abc import ABC, abstractmethod
from typing import Sequence, Union


class EventSender:

    def __init__(self, *parts: Sequence[Union[str, int]]):
        self._parts = [str(part) for part in parts]

    def __str__(self) -> str:
        return "::".join(self._parts)


class EventSenderObject(ABC):
    @property
    @abstractmethod
    def event_source(self) -> EventSender:
        pass

    def __str__(self):
        return self.event_source.__str__()


EventSenderParam = Union[str, EventSender, EventSenderObject]
