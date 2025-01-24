from typing import Optional, List, TYPE_CHECKING

from llama_index.core.chat_engine.types import ChatMode
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.openai import OpenAI

from applications.llama_index.index.two_steps.two_steps_vectorindex import (
    TwoStepsVectorIndex,
)
from conf.config import Config
from core.context.global_context import Context

if TYPE_CHECKING:
    from llama_index.core.base.llms.types import ChatMessage


class SessionContext(Context):
    @classmethod
    def get_context(cls, user_id="1") -> "SessionContext":

        session_id = "test"  # flask.request.sid  # type: ignore

        session_context = cls(sid=session_id)

        return session_context

    def __init__(self, sid, **kwargs) -> None:
        super().__init__(**kwargs)
        self._sid = sid

    @property
    def sid(self):
        return self._sid

    def get_chat_engine(
        self, conversation: str, chat_history: Optional[List["ChatMessage"]] = None
    ):

        llm = OpenAI(
            temperature=0.7,
            api_key="",  # FIXME
        )

        index = TwoStepsVectorIndex.for_elasticsearch(
            "arxiv-articles-2", Config()["ES_URL"], llm
        )

        memory = ChatMemoryBuffer.from_defaults(
            chat_history=chat_history, token_limit=3900
        )

        chat_engine = index.as_chat_engine(
            chat_mode=ChatMode.CONDENSE_QUESTION, memory=memory, verbose=True
        )

        return chat_engine
