from typing import TYPE_CHECKING, Mapping, Any

from llama_index.core.embeddings import resolve_embed_model
from llama_index.embeddings.huggingface.utils import DEFAULT_HUGGINGFACE_EMBEDDING_MODEL
from pydantic import Field

from core.models.a_model import AModel

if TYPE_CHECKING:
    from llama_index.core.base.embeddings.base import BaseEmbedding


class LIEmbeddings(AModel):
    META_MODEL = "llamaindex_embeddings"
    IS_ABSTRACT = True

    def as_embeddings(self) -> "BaseEmbedding":
        raise NotImplementedError


class LIEmbeddingsNone(LIEmbeddings):
    META_MODEL = "llamaindex_none_embeddings"

    def as_embeddings(self) -> "BaseEmbedding":
        return resolve_embed_model(None)

    @property
    def meta_label(self):
        return "none"


class LIEmbeddingsDefault(LIEmbeddings):
    META_MODEL = "llamaindex_default_embeddings"

    def as_embeddings(self) -> "BaseEmbedding":
        return resolve_embed_model("default")

    @property
    def meta_label(self):
        return "default"


class LIEmbeddingsClip(LIEmbeddings):
    META_MODEL = "llamaindex_clip_embeddings"

    def as_embeddings(self) -> "BaseEmbedding":
        return resolve_embed_model("clip")

    @property
    def meta_label(self):
        return "clip"


class LILocalEmbeddings(LIEmbeddings):
    META_MODEL = "llamaindex_hf_local_embeddings"

    embeddings_model_name: str = Field(
        DEFAULT_HUGGINGFACE_EMBEDDING_MODEL,
        alias="model_name",
        serialization_alias="model_name",
    )

    def as_embeddings(self) -> "BaseEmbedding":
        return resolve_embed_model(f"local:{self.embeddings_model_name}")

    @property
    def meta_label(self):
        return f"local:{self.embeddings_model_name}"

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **super().as_dict(**kwargs),
            "model_name": self.embeddings_model_name,
        }
