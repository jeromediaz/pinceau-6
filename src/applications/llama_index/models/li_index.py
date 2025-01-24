from abc import ABC
from typing import TYPE_CHECKING, Mapping, Any

from elasticsearch.helpers.vectorstore import AsyncBM25Strategy
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    MockEmbedding,
)
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from llama_index.vector_stores.elasticsearch import ElasticsearchStore

from conf import Config
from core.models.a_model import AModel

if TYPE_CHECKING:
    from llama_index.core.base.base_retriever import BaseRetriever
    from core.context.context import Context


class LiIndex(AModel, ABC):
    META_MODEL = "llamaindex_index"
    IS_ABSTRACT = True

    name: str

    @property
    def meta_label(self):
        return f"{self.name}"

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {**super().as_dict(**kwargs), "name": self.name}

    def as_index(self, context: "Context") -> "VectorStoreIndex":
        raise NotImplementedError

    def as_retriever(self, context: "Context", **kwargs) -> "BaseRetriever":
        return self.as_index(context).as_retriever(**kwargs)


class LiElasticFullTextIndex(LiIndex):
    IS_ABSTRACT = False
    META_MODEL = "llamaindex_elastic_fulltext_index"

    elastic_url_config: str = "ES_URL"

    index_name: str

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **super().as_dict(**kwargs),
            "elastic_url_config": self.elastic_url_config,
            "index_name": self.index_name,
        }

    def as_index(self, context: "Context") -> "VectorStoreIndex":
        vector_store = ElasticsearchStore(
            index_name=self.index_name,
            retrieval_strategy=AsyncBM25Strategy(),
            es_url=Config().get(self.elastic_url_config),
        )

        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        return VectorStoreIndex.from_vector_store(
            vector_store,
            llm=None,
            embed_model=MockEmbedding(embed_dim=1),
            storage_context=storage_context,
            node_parser=None,
        )

    def as_retriever(self, context: "Context", **kwargs) -> "BaseRetriever":
        kwargs.setdefault("vector_store_query_mode", VectorStoreQueryMode.TEXT_SEARCH)

        return self.as_index(context).as_retriever(**kwargs)


class LiElasticVectorIndex(LiIndex):
    META_MODEL = "llamaindex_elastic_vector_index"

    elastic_url_config: str = "ES_URL"
    index_name: str
    embed_model_str: str = "local:BAAI/bge-small-en-v1.5"

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **super().as_dict(**kwargs),
            "elastic_url_config": self.elastic_url_config,
            "index_name": self.index_name,
            "embed_model_str": self.embed_model_str,
        }

    def as_index(self, context: "Context") -> "VectorStoreIndex":
        vector_store = ElasticsearchStore(
            index_name=self.index_name,
            es_url=Config().get(self.elastic_url_config),
        )

        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        return VectorStoreIndex.from_vector_store(
            vector_store,
            llm=None,
            embed_model=self.embed_model_str,
            storage_context=storage_context,
        )

    def as_retriever(self, context: "Context", **kwargs) -> "BaseRetriever":
        filter_value = kwargs.pop("filter")

        vector_store_kwargs = None
        if filter_value:

            def custom_query(es_query, query):
                es_query["knn"]["filter"] = {"terms": filter_value}
                return es_query

            vector_store_kwargs = {"custom_query": custom_query}

        return self.as_index(context).as_retriever(
            **kwargs, vector_store_kwargs=vector_store_kwargs
        )
