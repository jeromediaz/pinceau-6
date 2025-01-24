from typing import List, Mapping, Any, TYPE_CHECKING, cast

from llama_index.core.schema import NodeWithScore, QueryBundle
from pydantic import BaseModel

from applications.llama_index.models.li_index import LiIndex
from core.database.mongodb import MongoDBHandler
from core.tasks.task import Task
from ui.helper import P6Field, FieldOptions

if TYPE_CHECKING:
    from core.context.context import Context


class LiChainedRetrieverTask(Task["LiChainedRetrieverTask.InputModel"]):

    class InputModel(BaseModel):
        query: str
        results: List[NodeWithScore]

    class OutputModel(BaseModel):
        results: List[NodeWithScore]

    class Parameters(BaseModel):
        from_field: str = "metadata.document_id"
        to_field: str = "metadata.doc_id"

        index_object_id: str = P6Field(
            options=FieldOptions.FULL_WIDTH,
            json_schema_extra={
                "type": "reference",
                "reference": "data/mongodb/llamaindex_index",
                "optional": False,
            },
        )
        top_k: int = 10

    async def _process(
        self, context: "Context", input_data: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        data_input_object = self.input_object(input_data)
        params_object = cast(
            LiChainedRetrieverTask.Parameters, self.merge_params(input_data)
        )

        li_index = MongoDBHandler.from_default(context).get_instance(
            LiIndex, "llamaindex_index", params_object.index_object_id
        )

        value_set = set()

        for node in data_input_object.results:
            value_set.add(node.metadata.get("arxiv id"))

        filter_object = {params_object.to_field: list(value_set)}

        retriever = li_index.as_retriever(
            context, similarity_top_k=params_object.top_k, filter=filter_object
        )
        results = retriever.retrieve(QueryBundle(query_str=data_input_object.query))

        return {"results": results}
