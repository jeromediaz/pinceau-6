import json
from typing import Mapping, Any, TYPE_CHECKING

from keybert import KeyBERT
from pydantic import BaseModel, Field

from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context


class ExtractKeywordsBertTask(Task):

    class UI(BaseModel):
        keywords: str = Field("Keywords")

    class InputModel(BaseModel):
        message: str

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        data_input_object = self.input_object(data_input)

        kw_model = KeyBERT()
        keywords = kw_model.extract_keywords(data_input_object.message)

        result_as_json = json.dumps(keywords)
        await context.event(self, "data", {"keywords": result_as_json})

        return {"keywords": keywords, **data_input}
