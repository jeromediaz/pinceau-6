from typing import TYPE_CHECKING, List, Mapping, Any, cast

from pydantic import BaseModel

from applications.chat.models.a_chat_message import AChatMessage, MessageStatus
from applications.chat.models.chat_text_message import ChatTextMessage
from applications.chat.tasks import BaseChatTask
from core.context.chat_context import ChatContext
from core.database.mongodb import MongoDBHandler
from core.tasks.types import TaskEdgeKind

if TYPE_CHECKING:
    from core.tasks.task_node import TaskNode
    from core.context.context import Context


class ChatUserBranchingTask(BaseChatTask):

    class OutputModel(BaseModel):
        message: str

    class InputModel(BaseModel):
        chat_id: str
        message: str

    def __init__(self, default: str, **kwargs):
        super().__init__(**kwargs, is_passthrough=True)
        self._tasks_after: list[str] = []
        self._default = default

    def clone(self, **kwargs) -> "BaseChatTask":
        return self.__class__(self._default, **self.params, **kwargs)

    def tasks_after(
        self, node: "TaskNode", for_mode: TaskEdgeKind = TaskEdgeKind.DEFAULT
    ) -> List[str]:
        return self._tasks_after

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        chat_context = context.cast_as(ChatContext)

        data_input_object = self.input_object(data_input)

        message = data_input_object.message
        first_token = message.strip().split()[0]

        next_task_id = self._default

        if first_token.startswith("@"):
            message = message.replace(first_token, "").strip()
            agent_name = first_token[1:]
            if agent_name[-1] == ":":
                agent_name = agent_name[:-1]

            node = self.node

            if node is None:
                raise ValueError("Need to be called inside a DAG")

            if agent_name in [sub_node.to_id for sub_node in node.sub_nodes]:
                next_task_id = agent_name

        self._tasks_after = [next_task_id]

        to_user = f"agent:{next_task_id}"
        context.set("to_user", to_user)

        input_message_raw: dict | AChatMessage = context.get("input_message")
        if isinstance(input_message_raw, dict):
            input_message_raw["_id"] = input_message_raw.pop("id")
            input_message = cast(
                AChatMessage, MongoDBHandler.load_object(input_message_raw)
            )
        else:
            input_message = input_message_raw

        input_message.status = MessageStatus.READ
        if isinstance(input_message, ChatTextMessage):
            input_message.to_user = to_user
        await chat_context.update_message(context, input_message)

        return {**data_input, "message": message}
