from typing import Mapping, Any, Optional, TYPE_CHECKING, Dict

from ui.fieldable import Fieldable

if TYPE_CHECKING:
    from core.tasks.task import Task


class ChordDiagramField(Fieldable):

    source: Optional[str] = None
    component_id: int = 1

    def as_ui_field(self, for_task: Optional["Task"] = None) -> Mapping[str, Any]:
        options: Dict[str, Any] = {}

        field: Dict[str, Any] = {}

        if self.source:
            field["source"] = self.source

        field.update({
            "type": "chord_diagram",
            "options": options,
            "componentId": self.component_id,
        })

        return field
