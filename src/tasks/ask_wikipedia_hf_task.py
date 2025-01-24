from typing import TYPE_CHECKING, Mapping, Any, cast

from llama_index.core import StorageContext, ServiceContext, VectorStoreIndex, Response
from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from pydantic import BaseModel

from conf.config import Config
from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context


class AskWikipediaHFTask(Task):

    class InputModel(BaseModel):
        question: str

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        input_model_object = self.input_object(data_input)

        es = ElasticsearchStore(index_name="wikipedia", es_url=Config()["ES_URL"])

        remotely_run = HuggingFaceInferenceAPI(
            model_name="HuggingFaceH4/zephyr-7b-alpha",
        )

        storage_context = StorageContext.from_defaults(vector_store=es)
        service_context = ServiceContext.from_defaults(
            embed_model="local:BAAI/bge-small-en-v1.5",
            llm=remotely_run,
        )
        index = VectorStoreIndex.from_vector_store(
            es, service_context=service_context, storage_context=storage_context
        )

        query_engine = index.as_query_engine(streaming=False)

        question = input_model_object.question

        response: Response = cast(Response, query_engine.query(question))

        text_response = response.response
        if text_response is not None:
            await context.event(self, "stream", {"answer": (text_response, False)})

        print(response.get_formatted_sources())

        return {"response": response}
