import hashlib
import logging
from typing import Mapping, Any, cast, Optional

from pydantic import BaseModel

from applications.arxiv.tasks.index_arxiv_result import IndexArxivResult
from applications.llama_index.index.two_steps.two_steps_vectorindex import (
    TwoStepsVectorIndex,
)
from conf.config import Config

logging.basicConfig(level=logging.DEBUG)


def _hacky_hash(some_string):
    return hashlib.md5(some_string.encode("utf-8")).hexdigest()


class SearchArxivResultPDF(IndexArxivResult):

    class InputModel(BaseModel):
        query: str

    def __init__(self) -> None:
        super().__init__()

        self._index_vector_store: Optional[TwoStepsVectorIndex] = None

    @property
    def index_vector_store(self) -> TwoStepsVectorIndex:
        if not self._index_vector_store:
            self._index_vector_store = TwoStepsVectorIndex.for_elasticsearch(
                "arxiv-articles", Config()["ES_URL"]
            )

        return cast(TwoStepsVectorIndex, self._index_vector_store)

    async def _process(self, context, data_in: Mapping[str, Any]) -> Mapping[str, Any]:
        index = data_in["index"]()

        print(index.as_chat_engine().chat(data_in.get("query")))

        return {}
