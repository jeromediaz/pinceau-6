from typing import Mapping, Any, TYPE_CHECKING

from pydantic import BaseModel

from applications.chat.tasks import BaseChatTask

if TYPE_CHECKING:
    from core.context.context import Context


class ChatTask(BaseChatTask):

    class OutputModel(BaseModel):
        answer: str

    class InputModel(BaseModel):
        chat_id: str
        message: str

    def __init__(self, handler, **kwargs):
        super().__init__(is_passthrough=True, **kwargs)
        self._handler = handler

    def clone(self, **kwargs) -> "BaseChatTask":
        return self.__class__(self._handler, **self.params, **kwargs)

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        return await self._handler(context, **data_input)
