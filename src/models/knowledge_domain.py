import datetime
from typing import ClassVar, Any, Mapping, cast

from pydantic import BaseModel

from core.models.a_model import AModel
from core.models.types import ModelUsageMode


class IngestedDocument(BaseModel):
    date: datetime.datetime


class KnowledgeDomain(AModel):

    META_MODEL: ClassVar[str] = "knowledge_domain"

    index: str
    name: str
    description: str

    ingestions: list[str] = []

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **self.model_dump(mode="json", by_alias=True),
            "_meta": {"label": self.meta_label},
        }

    @property
    def meta_label(self) -> str:
        if not self.model_extra:
            return super().meta_label

        return cast(str, self.model_extra.get("label"))

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        return [
            {"source": "label", "type": "text"},
            {"source": "index", "type": "text"},
            {"source": "name", "type": "text"},
            {"source": "description", "type": "text"},
            {
                "source": "ingestions",
                "type": "reference",
                "multiple": True,
                "reference": "data/mongodb/ingestion",
            },
        ]
