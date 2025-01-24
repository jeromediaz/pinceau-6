from typing import Optional, List, Dict, cast, Callable, Mapping, Any

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from applications.chat.models.a_chat import AChat
from applications.chat.models.a_chat_message import AChatMessage
from applications.chat.models.chat_photo_message import ChatPhotoMessage
from applications.chat.models.chat_system_message import ChatSystemMessage
from applications.chat.models.chat_text_message import ChatTextMessage
from core.context.global_context import Context, GlobalContext
from core.database.mongodb import MongoDBHandler


class ChatContext(Context):
    loaded_chats: Dict[str, "ChatContext"] = dict()

    @classmethod
    def get_context(cls, chat_id: str) -> "ChatContext":
        context = GlobalContext.get_instance()

        mongo_db_handler = MongoDBHandler.from_default(context)

        message_list = list(
            mongo_db_handler.load_multiples("chat_messages", {"chat_id": chat_id})
        )

        chat_context = ChatContext(chat_id=chat_id, message_list=message_list)

        cls.loaded_chats[chat_id] = chat_context

        return chat_context

    def __init__(
        self, chat_id, message_list: Optional[List["AChatMessage"]] = None, **kwargs
    ) -> None:
        super().__init__(**kwargs)

        chat_object = AChat.load_from_mongo(chat_id)
        if chat_object is None:
            raise ValueError(f"Unable to load chat for id {chat_id}")

        self._chat_object: AChat = chat_object

        self._chat_id = chat_id
        self._message_list = message_list.copy() if message_list else []

    def serialize(self) -> Mapping[str, Any]:
        return {
            **super().serialize(),
            "chat_id": self._chat_id,
            "message_list": [msg.as_dict() for msg in self._message_list],
        }

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> "ChatContext":
        message_list = []

        for message_data in data["message_list"]:
            message_data["_id"] = message_data.pop("id")
            message_list.append(
                cast(AChatMessage, MongoDBHandler.load_object(message_data))
            )

        return cls(data["chat_id"], message_list)

    @property
    def chat_id(self) -> str:
        return self._chat_id

    async def update_message(self, context: "Context", message: AChatMessage):
        db_manager = MongoDBHandler.from_default(context)

        db_manager.update_object(
            context, message, "chat_messages"
        )  # TODO: check context

        await context.event(
            f"chat::{self._chat_id}",
            "chatResponse",
            {
                "chatId": self._chat_id,
                "messages": [message.to_json_dict()],
            },
        )

    async def add_message(
        self, context: "Context", message: AChatMessage
    ) -> AChatMessage:
        self._message_list.append(message)

        db_manager = MongoDBHandler.from_default(context)
        db_manager.save_object(context, message, "chat_messages")  # TODO: check context

        print("context onEvent chatResponse")
        await context.event(
            f"chat::{self._chat_id}",
            "chatResponse",
            {"chatId": self._chat_id, "messages": [message.to_json_dict()]},
        )

        return message

    async def add_system_message(
        self, context: "Context", message: str, from_user: str, **kwargs
    ) -> ChatSystemMessage:
        new_message = ChatSystemMessage(
            chat_id=self._chat_id,
            text=message,
            message_index=len(self._message_list),
            from_user=from_user,
            **kwargs,
        )

        return cast(ChatSystemMessage, await self.add_message(context, new_message))

    async def add_text_message(
        self,
        context: "Context",
        message: str,
        from_user: str,
        to_user: str,
        position: str,
        **kwargs,
    ) -> ChatTextMessage:
        new_message = ChatTextMessage(
            chat_id=self._chat_id,
            text=message,
            message_index=len(self._message_list),
            from_user=from_user,
            to_user=to_user,
            position=position,
            **kwargs,
        )

        return cast(ChatTextMessage, await self.add_message(context, new_message))

    async def add_photo_message(
        self, context: "Context", uri: str, from_user: str, **kwargs
    ) -> ChatPhotoMessage:
        new_message = ChatPhotoMessage(
            chat_id=self._chat_id,
            uri=uri,
            message_index=len(self._message_list),
            from_user=from_user,
            **kwargs,
        )

        return cast(ChatPhotoMessage, await self.add_message(context, new_message))

    @property
    def message_list(self) -> List["AChatMessage"]:
        return self._message_list

    @property
    def last_message(self) -> Optional["AChatMessage"]:
        if self._message_list:
            return self._message_list[-1]
        return None

    @property
    def chat(self) -> AChat:
        return self._chat_object

    @staticmethod
    def chat_history_filter_function_factory(
        from_user: str, to_user: str
    ) -> Callable[[AChatMessage], bool]:
        def filter_function(message: AChatMessage) -> bool:
            if message.type != "text":
                return False

            if message.from_user not in [from_user, to_user]:
                return False
            if message.to_user not in [from_user, to_user]:
                return False

            if message.from_user == from_user and message.to_user == to_user:
                return True

            if message.from_user == to_user and message.to_user == from_user:
                return True

            return False

        return filter_function

    def extract_chat_history(self, from_user: str, to_user: str) -> List[ChatMessage]:
        filter_function = self.chat_history_filter_function_factory(from_user, to_user)

        filtered_messages = filter(filter_function, self.message_list)

        final_list: List[ChatMessage] = []

        for message in filtered_messages:
            base_text = message.text.strip()
            agent_annotation = f"@{message.to_user}"
            if base_text.startswith(f"@{message.to_user}"):
                base_text = base_text[len(agent_annotation) :].strip()
                if base_text.startswith(":"):
                    base_text = base_text[1:].strip()

            role = (
                MessageRole.USER
                if message.from_user == from_user
                else MessageRole.ASSISTANT
            )

            final_list.append(ChatMessage(role=role, content=base_text))

        return final_list
