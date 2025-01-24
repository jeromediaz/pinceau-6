from typing import List, Any

from core.models.a_model import AModel
from core.models.types import ModelUsageMode


class TestSubquery(AModel):
    META_MODEL = "test_subquery"

    @property
    def label(self):
        return self.model_extra.get("label", "")

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> List[Any]:
        return [
            {"source": "label", "type": "text"},
            {
                "source": "questions",
                "type": "text",
                "multiple": True,
                "hideOn": ["list"],
                "opts": ["fullWidth", "multiline"],
            },
            {
                "source": "models",
                "type": "text",
                "multiple": True,
                "render": "chip",
            },
            {
                "source": "tools",
                "type": "group",
                "multiple": True,
                "fields": [
                    {"source": "name", "type": "text"},
                    {"source": "description", "type": "text", "opts": ["fullWidth"]},
                ],
                "hideOn": ["list"],
            },
        ]
