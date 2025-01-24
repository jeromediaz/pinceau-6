import uuid
from abc import ABC
from typing import TYPE_CHECKING, Iterable, Optional

from core.tasks.types import Status

if TYPE_CHECKING:
    from core.context.context import Context


class GraphElement(ABC):
    def __init__(self, id: str = "", label: str = "", **kwargs):
        self._status = Status.IDLE
        self._id = id if id else str(uuid.uuid4())
        self._label = label if label else self.__class__.__name__

        self._description = kwargs.get("description", "")

        self._tags = kwargs.get("tags", [])
        self._error: Optional[Exception] = None
        self._parent_id = kwargs.get("parent_id", None)

    def as_json(self):
        dict_value = {
            "id": self._id,
            "label": self._label,
            "description": self._description,
            "status": self._status.name,
            "tags": self._tags,
            "error": str(self._error),
        }
        if self.parent_id:
            dict_value["parentId"] = self.parent_id

        return dict_value

    @property
    def id(self) -> str:
        return self._id

    @property
    def parent_id(self) -> Optional[str]:
        return self._parent_id

    @property
    def label(self) -> str:
        return self._label

    @property
    def status(self) -> Status:
        return self._status

    @property
    def description(self) -> str:
        return self._description

    @property
    def tags(self) -> Iterable[str]:
        return self._tags.copy()

    @property
    def error(self) -> Optional[Exception]:
        return self._error

    def set_status(
        self,
        context: "Context",
        value: Status,
        /,
        *,
        error: Optional[Exception] = None,
        **kwargs,
    ):
        self._status = value
        self._error = error if self._status == Status.ERROR else None
