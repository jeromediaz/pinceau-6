from typing import Mapping, Any, TYPE_CHECKING

from llama_index.core import (
    download_loader,
    KnowledgeGraphIndex,
    ServiceContext,
)
from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
from pydantic import BaseModel
from pyvis.network import Network

from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context


class InputToGraphTask(Task):

    class InputModel(BaseModel):
        text: str
        query: str
        output: str

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        data_input_object = self.input_object(data_input)

        StringIterableReader = download_loader("StringIterableReader")

        loader = StringIterableReader()
        documents = loader.load_data(texts=[data_input_object.textt])

        llm = HuggingFaceInferenceAPI(
            model_name="HuggingFaceH4/zephyr-7b-beta",
        )

        space_name = "llamaindex"
        edge_types, rel_prop_names = ["relationship"], [
            "relationship"
        ]  # default, could be omit if create from an empty kg
        tags = ["entity"]  # default, could be omit if create from an empty kg

        service_context = ServiceContext.from_defaults(
            embed_model="local:BAAI/bge-small-en-v1.5",
            llm=llm,
            chunk_size_limit=512,
        )

        kg_index = KnowledgeGraphIndex.from_documents(
            documents,
            service_context=service_context,
            max_triplets_per_chunk=10,
            space_name=space_name,
            edge_types=edge_types,
            rel_prop_names=rel_prop_names,
            tags=tags,
            include_embeddings=True,
        )

        g = kg_index.get_networkx_graph()
        net = Network(notebook=True, cdn_resources="in_line", directed=True)
        net.from_nx(g)
        net.show(data_input_object.output + ".html")

        query_engine = kg_index.as_query_engine(
            include_text=False  # , response_mode="tree_summarize"
        )

        resp = query_engine.query(data_input_object.query)

        print(resp)

        return {}
