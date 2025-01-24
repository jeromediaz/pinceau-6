from typing import cast

from llama_index.core import Document
from pydantic import BaseModel

from applications.llama_index.models.li_index import LiIndex
from applications.llama_index.models.li_node_parser import LiNodeParser
from core.context.context import Context
from core.database.mongodb import MongoDBHandler
from core.tasks.task import Task
from core.tasks.types import TaskData
from ui.helper import P6ReferenceField


class LiIngestDocumentTask(Task["LiIngestDocumentTask.InputModel"]):

    class InputModel(BaseModel):
        class Config:
            arbitrary_types_allowed = True

        document: Document

    class Parameters(BaseModel):
        index_object_id: str = P6ReferenceField(
            reference="data/mongodb/llamaindex_index"
        )
        node_parser: str = P6ReferenceField(
            reference="data/mongodb/llamaindex_node_parser"
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._index = None
        self._node_parser = None

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        params_object = cast(
            LiIngestDocumentTask.Parameters, self.merge_params(data_in)
        )

        input_object = self.input_object(data_in)

        db_handler = MongoDBHandler.from_default(context)

        if not self._index:
            self._index = db_handler.get_instance(
                LiIndex, "llamaindex_index", params_object.index_object_id
            ).as_index(context)

        if not self._node_parser:
            self._node_parser = db_handler.get_instance(
                LiNodeParser, "llamaindex_node_parser", params_object.node_parser
            ).as_node_parser()

        document = input_object.document

        nodes = self._node_parser.get_nodes_from_documents([document])

        self._index.insert_nodes(nodes)

        return {}
