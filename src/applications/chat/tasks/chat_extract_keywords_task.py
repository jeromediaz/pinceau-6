import json
import os
from typing import TYPE_CHECKING, Mapping, Any, Sequence

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel

from applications.chat.tasks import BaseChatTask
from core.context.chat_context import ChatContext

if TYPE_CHECKING:
    from core.context.context import Context


class ChatExtractKeywordsTask(BaseChatTask):

    class InputModel(BaseModel):
        chat_id: str
        message: str

    class OutputModel(BaseModel):
        keywords: Sequence[str]

    async def _process(self, context: "Context", data_input: Mapping[str, Any]):
        data_input_object = self.input_object(data_input)

        chat_context = context.cast_as(ChatContext)

        os.environ.setdefault(
            "OPENAI_API_KEY",
        )

        llm = OpenAI(temperature=0.0)

        system_message = ChatMessage(
            role=MessageRole.SYSTEM,
            content="Extract from the user input what subjects the user want to lean about. Answer using JSON format.",
        )
        user_message = ChatMessage(
            role=MessageRole.USER, content=f"INPUT: {data_input_object.message}"
        )

        chat_response = llm.chat([system_message, user_message])

        content = chat_response.message.content

        keywords = []
        try:
            content_as_json = json.loads(content)
            first_key = next(iter(content_as_json))
            subjects = content_as_json.get(first_key)

            if isinstance(subjects, str):
                keywords = [subjects]
            elif isinstance(subjects, list):
                keywords = subjects

            content = f"Subjects: {', '.join(keywords)}"
        except Exception as e:
            content = f"Exception {e} parsing answer {content}"

        await chat_context.add_system_message(context, content, "agent:system")

        return {**data_input, "keywords": keywords}
