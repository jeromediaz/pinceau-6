import hashlib
import logging
from typing import TYPE_CHECKING, Mapping, Any, cast

import arxiv
from pydantic import BaseModel, Field

from applications.arxiv.tasks.index_arxiv_result import IndexArxivResult
from core.tasks.task import Task
from core.tasks.types import TaskData
from misc.mongodb_helper import mongodb_collection

if TYPE_CHECKING:
    from core.context.context import Context

logging.basicConfig(level=logging.DEBUG)


def _hacky_hash(some_string):
    return hashlib.md5(some_string.encode("utf-8")).hexdigest()


class ArxivTitleCategoryPrepareIndexTask(Task):

    class Parameters(BaseModel):
        collection: str = Field(default="ingestion3")
        db_link: str = Field(default="mongodb")
        database: str = Field(default="pinceau6")

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        params = cast(
            ArxivTitleCategoryPrepareIndexTask.Parameters, self.merge_params(data_in)
        )

        mongo_collection = mongodb_collection(
            context, params.db_link, params.database, params.collection
        )

        mongo_collection.create_index(
            "arxiv_id",
            unique=False,
        )

        return {}


class StoreArxivTitleCategory(IndexArxivResult):

    class InputModel(BaseModel):
        class Config:
            arbitrary_types_allowed = True

        result: arxiv.Result

    class OutputModel(BaseModel):
        data: dict

    def __init__(self, **kwargs) -> None:
        kwargs.pop("is_passthrough", True)
        super().__init__(is_passthrough=True, **kwargs)

    async def _process(self, context, data_in: Mapping[str, Any]) -> Mapping[str, Any]:
        data_object = self.input_object(data_in)

        result: arxiv.Result = data_object.result

        metadata = {
            "arxiv_id": result.entry_id,
            "category": result.primary_category,
            "title": result.title,
            "summary": result.summary,
        }

        return {**data_in, "data": metadata}
