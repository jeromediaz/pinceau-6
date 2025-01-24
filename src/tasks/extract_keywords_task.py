from typing import Mapping, Any, TYPE_CHECKING

import nltk
from llama_index.core.indices.keyword_table.utils import rake_extract_keywords
from pydantic import BaseModel

from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context


class ExtractKeywordsTask(Task):

    class InputModel(BaseModel):
        input: str

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:

        data_input_object = self.input_object(data_input)

        nltk.download("stopwords")

        keyword_input = data_input_object.input

        keywords = rake_extract_keywords(keyword_input, expand_with_subtokens=True)

        await context.event(
            self, "stream", {"answer": (", ".join(list(keywords)), False)}
        )

        return {"keywords": keywords}
