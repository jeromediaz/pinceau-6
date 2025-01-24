from typing import Mapping, Any, TYPE_CHECKING, cast, Optional

from llama_index.core import Document
from pydantic import BaseModel

from applications.llama_index.models.li_node_parser import LiNodeParser
from core.context.global_context import GlobalContext
from core.database.mongodb import MongoDBHandler
from core.models.a_model import AModel
from core.tasks.task import Task
from core.tasks.types import TaskData, TaskDataAsyncIterator
from models.knowledge_graph import KnowledgeGraph

if TYPE_CHECKING:
    from core.context.context import Context


class AModelExtractorTask(Task["AModelExtractorTask.InputModel"]):

    class InputModel(BaseModel):
        model_object: AModel
        node_parser: Optional[LiNodeParser] = None

    class Parameters(BaseModel):
        extract_key: str
        output_var: str

    class OutputModel(BaseModel):
        text: str

    async def _generator_process(
        self, context: "Context", input_data: TaskData
    ) -> TaskDataAsyncIterator:
        model: KnowledgeGraph = input_data["model_object"]
        value = cast(str, model.as_dict().get("text"))

        model.triplets = []

        node_parser_model = cast(Optional[LiNodeParser], input_data.get("node_parser"))
        if node_parser_model:
            node_parser = node_parser_model.as_node_parser()

            single_document = Document(text=value)

            for node in node_parser.get_nodes_from_documents([single_document]):
                if hasattr(node, "text"):
                    yield {**input_data, "text": getattr(node, "text")}

        else:
            yield {**input_data, "text": value}


class AModelUpdatorTask(Task["AModelExtractorTask.InputModel"]):

    class InputModel(BaseModel):
        model_object: AModel

    async def _process(
        self, context: "Context", input_data: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        context = GlobalContext.get_instance()

        model: AModel = input_data["model_object"]
        triplets = input_data["triplets"]
        model.triplets.extend(triplets)

        MongoDBHandler.from_default(context).save_object(context, model)

        return {**input_data}
