import asyncio
import logging
from typing import Optional, TYPE_CHECKING, Mapping, Any, Sequence, cast, List

from llama_index.core import (
    StorageContext,
    ServiceContext,
    VectorStoreIndex,
    Document,
    download_loader,
)
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from pydantic import BaseModel
from unidecode import unidecode

from conf.config import Config
from core.context.chat_context import ChatContext
from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context

logging.basicConfig(level=logging.DEBUG)


class IndexArxivTask(Task):

    class InputModel(BaseModel):
        keywords: str | List[str]

    class OutputModel(BaseModel):
        pass

    def __init__(self, work_index: int = -1, **kwargs):
        super().__init__(**kwargs)
        self._work_index = work_index

    def clone(self, work_index: Optional[int] = None, **kwargs) -> "Task":
        final_index = work_index if work_index is not None else self._work_index
        copy_params = dict(self.params)

        if work_index is not None:
            copy_params["id"] = f"{self.id}_{work_index}"
            copy_params["label"] = f"{self.label} - {work_index}"

        return self.__class__(
            final_index,
            **copy_params,
            **kwargs,
        )

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:

        chat_context = context.cast_as(ChatContext)

        if not isinstance(chat_context, ChatContext):
            raise ValueError(
                f"{self.__class__.__name__} context should be a ChatContext"
            )

        data_input_object = self.input_object(data_input)

        ArxivReader = download_loader("ArxivReader")
        graph_store = SimpleGraphStore()

        es = ElasticsearchStore(index_name="arxiv", es_url=Config()["ES_URL"])

        loader = ArxivReader()

        if not hasattr(loader, "load_papers_and_abstracts"):
            raise ValueError("loader has no required load_papers_and_abstracts method")

        search_query_list = data_input_object.keywords

        if not search_query_list:
            return {**data_input}

        if len(search_query_list) > 1:
            if self._work_index == -1:
                work_dag = self.dag()

                self_node = self.node

                if self_node is None or work_dag is None:
                    raise ValueError("Must be called inside a DAG")

                next_node_ids = self_node.sub_nodes.copy()
                next_node_tasks = list(
                    map(
                        lambda task_id: work_dag.task_node_map[task_id].task,
                        next_node_ids,
                    )
                )

                for next_node_id in next_node_ids:
                    work_dag.remove_parent_task(next_node_id, self)

                for query_index in range(len(search_query_list)):
                    sub_task = self.clone(query_index, dag=work_dag)

                    work_dag.add_child_task(self, sub_task)

                    for next_task in next_node_tasks:
                        work_dag.add_child_task(sub_task, next_task)

                return {**data_input}

            search_query_list = [search_query_list[self._work_index]]

        search_query = search_query_list[0]

        await context.event(
            self,
            "data",
            {"current_query": search_query, "retry_count": "-", "result_count": "-"},
        )

        documents: Sequence[Document] = []
        abstracts: Sequence[Document] = []
        retry_count = 0
        while not documents:
            await context.event(self, "data", {"retry_count": str(retry_count)})
            try:
                documents, abstracts = loader.load_papers_and_abstracts(
                    search_query=search_query,
                    max_results=10,
                    papers_dir=f".papers_{self._work_index}",
                )
            except Exception as e:
                print(e)

            await context.event(self, "data", {"result_count": str(len(documents))})

            if not documents:
                await asyncio.sleep(300)
                retry_count += 1

        for doc in documents:
            if "URL" in doc.metadata:
                doc.id_ = doc.metadata["URL"]

        for doc in abstracts:
            if "URL" in doc.metadata:
                doc.id_ = doc.metadata["URL"] + "#abstract"

        await chat_context.add_system_message(
            context,
            f"{len(documents)} article(s) extracted from arxiv for keyword {search_query}",
            "agent:system",
        )

        parser = SentenceSplitter()
        for doc in documents:
            doc.text = unidecode(doc.text)

        nodes = parser.get_nodes_from_documents(documents)

        uri = Config()["MONGODB_MM1_URI"]
        docstore = MongoDocumentStore.from_uri(uri=uri)

        storage_context = StorageContext.from_defaults(
            vector_store=es, graph_store=graph_store, docstore=docstore
        )

        service_context = ServiceContext.from_defaults(
            embed_model="local:BAAI/bge-small-en-v1.5",
            llm=None,
            chunk_size=512,
        )
        vector_index = VectorStoreIndex.from_vector_store(
            cast(BasePydanticVectorStore, es),
            service_context=service_context,
            storage_context=storage_context,
        )

        vector_index.insert_nodes(nodes)

        chat_context = context.cast_as(ChatContext)

        await chat_context.add_system_message(
            context,
            f"The article(s) have been ingested successfully for keyword {search_query}",
            "agent:system",
        )

        return {**data_input}
