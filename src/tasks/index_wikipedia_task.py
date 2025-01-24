from typing import Mapping, Any, TYPE_CHECKING

from llama_index.core import (
    download_loader,
    StorageContext,
    ServiceContext,
    VectorStoreIndex,
)
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from pydantic import BaseModel

from conf.config import Config
from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context


class IndexWikipediaTask(Task):

    class InputModel(BaseModel):
        subject: str

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        data_input_model = self.input_object(data_input)

        WikipediaReader = download_loader("WikipediaReader")

        es = ElasticsearchStore(index_name="wikipedia", es_url=Config()["ES_URL"])

        loader = WikipediaReader()
        documents = loader.load_data(pages=[data_input_model.sbject])
        storage_context = StorageContext.from_defaults(vector_store=es)
        service_context = ServiceContext.from_defaults(
            embed_model="local:BAAI/bge-small-en-v1.5",
            llm=None,
        )

        VectorStoreIndex.from_documents(
            documents, storage_context=storage_context, service_context=service_context
        )

        return {}
