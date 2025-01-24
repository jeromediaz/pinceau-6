import datetime
import json
from typing import ClassVar, Dict, Any, Optional, Mapping

from pydantic import BaseModel

from core.models.a_model import AModel
from core.models.types import ModelUsageMode


class IngestedDocument(BaseModel):
    date: datetime.datetime


class Ingestion(AModel):

    META_MODEL: ClassVar[str] = "ingestion"

    data: Dict[str, Any]
    pipeline: str

    documents: Dict[str, IngestedDocument] = {}
    first_ingestion_date: datetime.datetime
    last_ingestion_run_date: datetime.datetime
    last_ingestion_finish_date: Optional[datetime.datetime] = None

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **self.model_dump(mode="json", by_alias=True),
            "_meta": {"label": self.meta_label},
        }

    @property
    def meta_label(self) -> str:
        return f"{self.pipeline} - {json.dumps(self.data)}"

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        return [
            {"source": "label", "type": "text"},
            {
                "source": "pipeline",
                "type": "text",
                "multiple": False,
            },
        ]
