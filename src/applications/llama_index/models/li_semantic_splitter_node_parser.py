from typing import TYPE_CHECKING, Optional

from llama_index.core.node_parser.text.semantic_splitter import (
    DEFAULT_OG_TEXT_METADATA_KEY,
    SemanticSplitterNodeParser,
)

from applications.llama_index.models.li_embeddings import LIEmbeddings
from applications.llama_index.models.li_node_parser import LiNodeParser

if TYPE_CHECKING:
    from llama_index.core.node_parser import NodeParser


class LiSemanticSplitterNodeParser(LiNodeParser):
    META_MODEL = "llamaindex_semantic_splitter_node_parser"

    embed_model: LIEmbeddings
    breakpoint_percentile_threshold: Optional[int] = 95
    buffer_size: Optional[int] = 1
    original_text_metadata_key: str = DEFAULT_OG_TEXT_METADATA_KEY
    include_metadata: bool = True
    include_prev_next_rel: bool = True

    def as_node_parser(self) -> "NodeParser":
        return SemanticSplitterNodeParser.from_defaults(
            embed_model=self.embed_model.as_embeddings(),
            breakpoint_percentile_threshold=self.breakpoint_percentile_threshold,
            buffer_size=self.buffer_size,
            original_text_metadata_key=DEFAULT_OG_TEXT_METADATA_KEY,
            include_metadata=self.include_metadata,
            include_prev_next_rel=self.include_prev_next_rel,
        )
