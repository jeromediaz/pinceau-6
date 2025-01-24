from typing import Mapping, Any

from pydantic import Field

from applications.chat.models.a_chat_message import AChatMessage


class ChatTextMessage(AChatMessage):
    META_MODEL = "chat_text_message"

    type: str = "text"
    text: str = Field(default="")
    to_user: str
    position: str = Field(default="")

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **super().as_dict(**kwargs),
            "text": self.text,
            "position": self.position,
            "to_user": self.to_user,
        }
