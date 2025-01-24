from typing import Any, Dict, Sequence

from llama_index.core import VectorStoreIndex, ServiceContext, StorageContext
from llama_index.core.data_structs.data_structs import EmptyIndexStruct
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core.indices.base import BaseIndex
from llama_index.core.indices.base_retriever import BaseRetriever
from llama_index.core.llms import LLM
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.schema import BaseNode, Document
from llama_index.core.storage.docstore.types import RefDocInfo
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.elasticsearch import ElasticsearchStore

from applications.llama_index.index.two_steps.two_steps_vectorindex_retriever import (
    TwoStepsVectorIndexRetriever,
)
from applications.llama_index.models.li_pass_through_node_parser import (
    PassthroughTextSplitter,
)


class TwoStepsVectorIndex(BaseIndex[EmptyIndexStruct]):

    text_index: VectorStoreIndex
    vector_index: VectorStoreIndex

    def __init__(
        self,
        text_index: VectorStoreIndex,
        vector_index: VectorStoreIndex,
        llm: LLM,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.text_index = text_index
        self.vector_index = vector_index
        self._llm = llm

        self._first_text_doc = True
        self._first_vector_doc = True

    @classmethod
    def create_vectorstore_index(
        cls, index_name: str, es_url: str, text_mode: bool
    ) -> VectorStoreIndex:

        suffix = "text" if text_mode else "vector"

        vector_store = ElasticsearchStore(
            index_name=f"{index_name}_{suffix}", es_url=es_url
        )

        text_splitter = PassthroughTextSplitter() if text_mode else None
        node_parser = (
            None
            if text_mode
            else SemanticSplitterNodeParser.from_defaults(
                embed_model=resolve_embed_model("local:BAAI/bge-small-en-v1.5"),
                breakpoint_percentile_threshold=95,
            )
        )
        llm = None
        if text_mode:
            llm = OpenAI(
                temperature=0,
                api_key="",  # FIXME
            )

        service_context = ServiceContext.from_defaults(
            embed_model=None if text_mode else "local:BAAI/bge-small-en-v1.5",
            llm=llm,
            text_splitter=text_splitter,
            node_parser=node_parser,
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        return VectorStoreIndex.from_vector_store(
            vector_store,
            service_context=service_context,
            storage_context=storage_context,
        )

    @classmethod
    def for_elasticsearch(
        cls, base_index_name: str, es_url: str, llm=None
    ) -> "TwoStepsVectorIndex":

        text_index = cls.create_vectorstore_index(base_index_name, es_url, True)
        vector_index = cls.create_vectorstore_index(base_index_name, es_url, False)

        return cls(
            text_index=text_index,
            vector_index=vector_index,
            llm=llm,
            nodes=[],
            service_context=ServiceContext.from_defaults(llm=llm, embed_model=None),
        )

    def _build_index_from_nodes(
        self, nodes: Sequence[BaseNode], **insert_kwargs: Any
    ) -> EmptyIndexStruct:
        return EmptyIndexStruct()

    def insert_text(self, document: Document, **insert_kwargs: Any):
        self.text_index.insert(
            document, create_index_if_not_exists=self._first_text_doc, **insert_kwargs
        )
        self._first_text_doc = False

    def insert_vector(self, document: Document, **insert_kwargs: Any):
        self.vector_index.insert(
            document, create_index_if_not_exists=self._first_vector_doc, **insert_kwargs
        )
        self._first_vector_doc = False

    def insert(self, document: Document, **insert_kwargs: Any) -> None:
        # split document into two

        if "text_metadata_key" in insert_kwargs:
            metadata = document.metadata
            text_value = metadata.pop(insert_kwargs["text_metadata_key"])

            text_document = Document(
                doc_id=document.doc_id, text=text_value, extra_info=metadata
            )
            vector_document = Document(
                doc_id=document.doc_id, text=document.text, extra_info=metadata
            )

            self.text_index.insert(text_document)
            self.vector_index.insert(vector_document)

        else:
            self.text_index.insert(document)
            self.vector_index.insert(document)

    def delete_ref_doc(
        self, ref_doc_id: str, delete_from_docstore: bool = False, **delete_kwargs: Any
    ) -> None:
        self.text_index.delete_ref_doc(
            ref_doc_id, delete_from_docstore=delete_from_docstore, **delete_kwargs
        )
        self.vector_index.delete_ref_doc(
            ref_doc_id, delete_from_docstore=delete_from_docstore, **delete_kwargs
        )

    def _insert(self, nodes: Sequence[BaseNode], **insert_kwargs: Any) -> None:
        return

    def _delete_node(self, node_id: str, **delete_kwargs: Any) -> None:
        return

    @property
    def ref_doc_info(self) -> Dict[str, RefDocInfo]:
        return self.text_index.ref_doc_info

    def as_retriever(self, **kwargs: Any) -> BaseRetriever:
        # 1) extract keywords
        # 2) perform text search
        # 3) fetch document id
        # 4) perform hybrid search on whose document id

        return TwoStepsVectorIndexRetriever(
            self.text_index, self.vector_index, self._llm
        )
