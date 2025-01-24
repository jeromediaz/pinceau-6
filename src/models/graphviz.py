from typing import ClassVar, Mapping, Any

from pydantic import Field

from core.models.a_model import AModel
from ui.graphviz_dot_field import GraphvizDotField
from ui.helper import FieldOptions, P6Field


class Graphviz(AModel):
    META_MODEL: ClassVar[str] = "graphviz"

    name: str

    dot: str = P6Field(
        options=FieldOptions.FULL_WIDTH
        | FieldOptions.MULTILINE
        | FieldOptions.HIDE_ON_LIST
    )
    dot_preview: GraphvizDotField = Field(GraphvizDotField(source="dot"), exclude=True)

    @property
    def meta_label(self) -> str:
        return self.name

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **super().as_dict(**kwargs),
            "dot": self.dot,
            "name": self.name,
        }
