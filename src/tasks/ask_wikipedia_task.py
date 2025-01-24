from typing import TYPE_CHECKING, Mapping, Any, cast

from llama_index.core import VectorStoreIndex
from llama_index.core.base.response.schema import StreamingResponse
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.llms.llama_cpp import LlamaCPP
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from pydantic import BaseModel, Field

from conf.config import Config
from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context


class AskWikipediaTask(Task):

    class UI(BaseModel):
        answer: str = Field("answer")

    class InputModel(BaseModel):
        question: str

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        input_model_object = self.input_object(data_input)

        from llama_index.core import StorageContext
        from llama_index.core import ServiceContext

        await context.event(self, "stream", {"answer": ("Processing question…", True)})

        es = ElasticsearchStore(index_name="wikipedia", es_url=Config()["ES_URL"])

        llm = LlamaCPP(
            model_path="/Volumes/Data/faraday/openhermes-2.5-mistral-7b.Q4_K_M.gguf",
            model_kwargs={"n_gpu_layers": 1, "stopwords": ["[/INST]"]},
            context_window=4096,
            max_new_tokens=3000,
        )

        storage_context = StorageContext.from_defaults(vector_store=es)
        service_context = ServiceContext.from_defaults(
            embed_model="local:BAAI/bge-small-en-v1.5",
            llm=llm,
        )
        index = VectorStoreIndex.from_vector_store(
            cast(BasePydanticVectorStore, es),
            service_context=service_context,
            storage_context=storage_context,
        )

        query_engine = index.as_query_engine(streaming=True)

        question = input_model_object.question

        streaming_response = cast(StreamingResponse, query_engine.query(question))

        response = ""
        is_first = True
        for text in streaming_response.response_gen:
            response += text

            await context.event(self, "stream", {"answer": (text, is_first)})

            is_first = False

        print(streaming_response.get_formatted_sources())

        return {"response": response}
