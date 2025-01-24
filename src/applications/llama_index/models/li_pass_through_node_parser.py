from typing import List

from llama_index.core.node_parser import TextSplitter, NodeParser

from applications.llama_index.models.li_node_parser import LiNodeParser


class PassthroughTextSplitter(TextSplitter):

    def split_text(self, text: str) -> List[str]:
        return [text]


class LiPassThroughNodeParser(LiNodeParser):
    META_MODEL = "llamaindex_passthrough_node_parser"

    @property
    def meta_label(self):
        return f"{self.__class__.name}: {self.name}"

    def as_node_parser(self) -> "NodeParser":
        return PassthroughTextSplitter()
