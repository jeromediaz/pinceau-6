import time
from enum import Enum
from typing import Mapping, Any
from uuid import uuid4

from pydantic import Field

from core.models.a_model import AModel


class MessageStatus(str, Enum):
    NONE = ""
    WAITING = "waiting"
    SENT = "sent"
    RECEIVED = "received"
    READ = "read"


class AChatMessage(AModel):
    META_MODEL = "chat_message"

    chat_id: str
    message_index: int
    uuid: str = Field(default_factory=lambda: uuid4().hex)
    from_user: str
    type: str
    date: int = Field(default_factory=lambda: int(time.time() * 1000))
    status: MessageStatus = Field(default=MessageStatus.NONE)

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        dict_value = {
            **super().as_dict(**kwargs),
            "chat_id": self.chat_id,
            "message_index": self.message_index,
            "from_user": self.from_user,
            "type": self.type,
            "date": self.date,
            "uuid": self.uuid,
        }
        if isinstance(self.status, str):
            dict_value["status"] = self.status
        elif isinstance(self.status, MessageStatus):
            dict_value["status"] = self.status.value

        return dict_value
