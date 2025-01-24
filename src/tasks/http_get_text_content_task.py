from typing import Mapping, Optional, Any, TYPE_CHECKING

import aiohttp
from pydantic import BaseModel

from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context


class HttpGetTextContentTask(Task["HttpGetTextContentTask.InputModel"]):

    class InputModel(BaseModel):
        url: str
        params: Optional[Mapping[str, str]] = None

    class OutputModel(BaseModel):
        content: str

    def __init__(self, headers: Optional[Mapping[str, str]] = None, **kwargs):
        kwargs.pop("is_passthrough", False)
        self._headers = {**headers} if headers else {}

        super().__init__(is_passthrough=True, headers=headers, **kwargs)

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        data_input_object = self.input_object(data_input)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                data_input_object.url,
                params=data_input_object.params,
                headers=self._headers,
            ) as response:
                text_response = await response.text()
                return {**data_input, "content": text_response}
