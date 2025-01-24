from typing import ClassVar, Mapping, Any, List, Set

from pydantic import Field

from core.models.a_model import AModel
from ui.graphviz_dot_field import GraphvizDotField
from ui.helper import P6Field, FieldOptions


class KnowledgeGraph(AModel):
    META_MODEL: ClassVar[str] = "knowledge_graph"

    HIDDEN_FIELDS_LIST: ClassVar[Set[str]] = {"dot", "dot_preview", "triplets"}

    name: str
    text: str = P6Field(
        options=FieldOptions.MULTILINE
        | FieldOptions.FULL_WIDTH
        | FieldOptions.HIDE_ON_LIST
    )
    triplets: List[List[str]] = []
    dot_preview: GraphvizDotField = Field(GraphvizDotField(source="dot"), exclude=True)

    @property
    def meta_label(self) -> str:
        return self.name

    @property
    def dot(self) -> str:
        content: List[str] = [
            "digraph knowledge_graph {",
            "    node [shape=circle]",
            "    layout=circo",
        ]

        node_text_set = set()
        leaf_text_set = set()

        for triplet_subject, triplet_predicate, triplet_object in self.triplets:
            triplet_subject = triplet_subject.replace('"', '\\"')
            triplet_object = triplet_object.replace('"', '\\"')
            node_text_set.add(triplet_subject)
            leaf_text_set.add(triplet_object)

        added_line = set()

        for text in node_text_set:
            if text in leaf_text_set:
                content.append(f'    "{text}" [shape=oval]')

        for text in leaf_text_set:
            if text not in node_text_set:
                content.append(f'    "{text}" [shape=note]')

        for triplet_subject, triplet_predicate, triplet_object in self.triplets:
            triplet_subject = triplet_subject.replace('"', '\\"')
            triplet_object = triplet_object.replace('"', '\\"')

            line = f'    "{triplet_subject}" -> "{triplet_object}" [label=<{triplet_predicate}>]'

            if line in added_line:
                continue

            added_line.add(line)

            content.append(line)

        content.append("}")

        return "\n".join(content)

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        values = {
            **super().as_dict(**kwargs),
            "text": self.text,
            "name": self.name,
            "dot": self.dot,
            "triplets": self.triplets,
        }

        return values
