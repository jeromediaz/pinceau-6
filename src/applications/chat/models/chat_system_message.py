from typing import Mapping, Any

from applications.chat.models.a_chat_message import AChatMessage


class ChatSystemMessage(AChatMessage):
    META_MODEL = "chat_system_message"

    type: str = "system"
    text: str

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **super().as_dict(**kwargs),
            "text": self.text,
        }
