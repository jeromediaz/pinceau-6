from abc import ABC
from typing import TYPE_CHECKING

from core.models.a_model import AModel

if TYPE_CHECKING:
    from llama_index.core.node_parser import NodeParser


class LiNodeParser(AModel, ABC):
    META_MODEL = "llamaindex_node_parser"
    IS_ABSTRACT = True

    name: str

    @property
    def meta_label(self):
        return f"{self.__class__.name}: {self.name}"

    def as_node_parser(self) -> "NodeParser":
        raise NotImplementedError
