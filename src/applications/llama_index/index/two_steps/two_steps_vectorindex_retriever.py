from typing import Optional, List, TYPE_CHECKING

from llama_index.core import VectorStoreIndex
from llama_index.core.indices.base_retriever import BaseRetriever
from llama_index.core.indices.keyword_table.utils import extract_keywords_given_response
from llama_index.core.prompts.default_prompts import (
    DEFAULT_QUERY_KEYWORD_EXTRACT_TEMPLATE,
)
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.vector_stores.types import VectorStoreQueryMode

if TYPE_CHECKING:
    from applications.llama_index.models.li_llm import LiLlm


class TwoStepsVectorIndexRetriever(BaseRetriever):

    def __init__(
        self,
        text_index: VectorStoreIndex,
        vector_index: VectorStoreIndex,
        llm: Optional["LiLlm"],
    ):
        super().__init__()
        self._text_index = text_index
        self._vector_index = vector_index
        self._llm = llm

        self._text_index_retriever = text_index.as_retriever(
            vector_store_query_mode=VectorStoreQueryMode.TEXT_SEARCH,
            similarity_top_k=10,
        )

    def _get_keywords_query(self, query: QueryBundle) -> Optional[QueryBundle]:
        try:
            llm = self._llm
            if not llm:
                raise RuntimeError("LLM should not be None at this point")

            response = llm.predict(
                DEFAULT_QUERY_KEYWORD_EXTRACT_TEMPLATE,
                max_keywords=10,
                question=query.query_str,
            )
            keywords = extract_keywords_given_response(
                response, start_token="KEYWORDS:"
            )

            return QueryBundle(query_str=", ".join(keywords))
        except Exception as e:
            print(e)

        return None

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        text_nodes_with_score = self._text_index_retriever.retrieve(
            QueryBundle(query_str=query_bundle.query_str)
        )

        arxiv_id_set = set()
        for node in text_nodes_with_score:
            arxiv_id_set.add(node.metadata.get("arxiv id"))

        def custom_query(es_query, query):
            es_query["knn"]["filter"] = {
                "terms": {"metadata.document_id": list(arxiv_id_set)}
            }
            return es_query

        vector_retriever = self._vector_index.as_retriever(
            vector_store_query_mode=VectorStoreQueryMode.DEFAULT,
            similarity_top_k=10,
            vector_store_kwargs={"custom_query": custom_query},
        )

        return vector_retriever.retrieve(QueryBundle(query_str=query_bundle.query_str))
