from typing import Mapping, Any

from applications.chat.models.a_chat_message import AChatMessage


class ChatPhotoMessage(AChatMessage):
    META_MODEL = "chat_photo_message"

    uri: str
    type: str = "photo"

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **super().as_dict(**kwargs),
            "uri": self.uri,
        }
