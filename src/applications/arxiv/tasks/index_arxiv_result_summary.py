import logging
from typing import TYPE_CHECKING, Mapping, Any, cast, Optional

import arxiv
from llama_index.core import (
    Document,
    StorageContext,
    ServiceContext,
    VectorStoreIndex,
    KeywordTableIndex,
)
from llama_index.llms.llama_cpp import LlamaCPP
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from llama_index.storage.index_store.mongodb import MongoIndexStore
from llama_index.vector_stores.elasticsearch import ElasticsearchStore

from applications.arxiv.tasks.index_arxiv_result import IndexArxivResult
from conf.config import Config

if TYPE_CHECKING:
    from core.context.context import Context

logging.basicConfig(level=logging.DEBUG)


class IndexArxivResultSummary(IndexArxivResult):

    def __init__(self) -> None:
        super().__init__()

        self._service_context: Optional[ServiceContext] = None
        self._storage_context: Optional[StorageContext] = None
        self._summary_index_vector_store: Optional[VectorStoreIndex] = None
        self._keyword_table_index: Optional[KeywordTableIndex] = None
        self._elasticsearch_store: Optional[ElasticsearchStore] = None

    @property
    def elasticsearch_store(self) -> ElasticsearchStore:
        if not self._elasticsearch_store:
            self._elasticsearch_store = ElasticsearchStore(
                index_name="arxiv-summary", es_url=Config()["ES_URL"]
            )

        return cast(ElasticsearchStore, self._elasticsearch_store)

    @property
    def storage_context(self) -> StorageContext:
        if not self._storage_context:
            uri = Config()["MONGODB_MM1_URI"]
            index_store = MongoIndexStore.from_uri(uri=uri)

            docstore = MongoDocumentStore.from_uri(uri=uri)

            storage_context = StorageContext.from_defaults(
                vector_store=self.elasticsearch_store,
                docstore=docstore,
                index_store=index_store,
            )

            self._storage_context = storage_context

        return cast(StorageContext, self._storage_context)

    @property
    def service_context(self) -> ServiceContext:
        if not self._service_context:
            llm = LlamaCPP(
                model_path="/Volumes/Data/faraday/openhermes-2.5-mistral-7b.Q4_K_M.gguf",
                model_kwargs={"n_gpu_layers": 1, "stopwords": ["[/INST]"]},
                context_window=4096,
                max_new_tokens=3000,
            )

            self._service_context = ServiceContext.from_defaults(
                embed_model="local:BAAI/bge-small-en-v1.5",
                llm=llm,
                chunk_size_limit=512,
            )

        return cast(ServiceContext, self._service_context)

    @property
    def summary_index_vector_store(self):
        if not self._summary_index_vector_store:
            self._summary_index_vector_store = VectorStoreIndex.from_vector_store(
                self.elasticsearch_store,
                service_context=self.service_context,
                storage_context=self.storage_context,
            )
        return self._summary_index_vector_store

    @property
    def keyword_table_index(self) -> KeywordTableIndex:
        if not self._keyword_table_index:
            self._keyword_table_index = KeywordTableIndex.from_documents(
                documents=[],
                storage_context=self.storage_context,
                service_context=self.service_context,
            )

        return self._keyword_table_index

    async def _process(
        self, context: "Context", data_in: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        data_object = self.input_object(data_in)

        result: arxiv.Result = data_object.result

        metadata = {
            "arxiv id": result.entry_id,
            "Title of this paper": result.title,
            "Authors": ", ".join([a.name for a in result.authors]),
            "Date published": result.published.strftime("%m/%d/%Y"),
            "Date updated": result.published.strftime("%m/%d/%Y"),
            "Primary category": result.primary_category,
            "Categories": ", ".join(result.categories),
        }

        d = f"The following is a summary of the paper: {result.title}\n\nSummary: {result.summary}"

        abstract_document = Document(
            doc_id=f"{result.entry_id}", text=d, extra_info=metadata
        )

        self.summary_index_vector_store.insert(abstract_document)
        self.keyword_table_index.insert(abstract_document)

        return {}
