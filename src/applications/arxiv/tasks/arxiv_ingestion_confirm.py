from typing import TYPE_CHECKING, Mapping, Any

import arxiv
from pydantic import BaseModel

from core.context.composite_context import CompositeContext
from core.tasks.task import Task
from models.ingestion import IngestedDocument, Ingestion

if TYPE_CHECKING:
    from core.context.context import Context


class ArxivIngestionConfirm(Task):
    class InputModel(BaseModel):
        class Config:
            arbitrary_types_allowed = True

        ingestion: Ingestion
        result: arxiv.Result
        success: bool

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        if not isinstance(context, CompositeContext):
            raise ValueError(
                f"{self.__class__.__name__} context should be a CompositeContext"
            )

        ingestion = data_input["ingestion"]
        result = data_input["result"]
        success = data_input["success"]

        if success:
            ingestion.documents[result.entry_id] = IngestedDocument(date=result.updated)

        return {**data_input}
