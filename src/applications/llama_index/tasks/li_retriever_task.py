from typing import List, TYPE_CHECKING, cast

from llama_index.core.schema import NodeWithScore, QueryBundle
from pydantic import BaseModel

from applications.llama_index.models.li_index import LiIndex
from core.database.mongodb import MongoDBHandler
from core.tasks.task import Task
from core.tasks.types import TaskData
from ui.helper import P6Field, FieldOptions

if TYPE_CHECKING:
    from core.context.context import Context


class LiRetrieverTask(Task["LiRetrieverTask.InputModel"]):

    class InputModel(BaseModel):
        query: str

    class OutputModel(BaseModel):
        results: List[NodeWithScore]

    class Parameters(BaseModel):
        index_object_id: str = P6Field(
            options=FieldOptions.FULL_WIDTH,
            json_schema_extra={
                "type": "reference",
                "reference": "data/mongodb/llamaindex_index",
                "optional": False,
            },
        )
        top_k: int = 10

    async def _process(self, context: "Context", input_data: TaskData) -> TaskData:
        data_input_object = self.input_object(input_data)
        params_object = cast(LiRetrieverTask.Parameters, self.merge_params(input_data))

        li_index = MongoDBHandler.from_default(context).get_instance(
            LiIndex, "llamaindex_index", params_object.index_object_id
        )

        print("before getting retriever")
        retriever = li_index.as_retriever(context, similarity_top_k=params_object.top_k)
        print(f"before query {data_input_object.query}")
        results = retriever.retrieve(QueryBundle(query_str=data_input_object.query))
        print(f"{results=}")
        return {"results": results}
