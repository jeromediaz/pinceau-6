from typing import Mapping, Any, Optional, TYPE_CHECKING

from ui.fieldable import Fieldable

if TYPE_CHECKING:
    from core.tasks.task import Task


class GraphvizDotField(Fieldable):

    source: Optional[str] = None

    def as_ui_field(self, for_task: Optional["Task"] = None) -> Mapping[str, Any]:
        options = {
            "fit": True,
            "height": None,
            "width": "100%",
            "zoom": False,
        }

        field = {}
        if self.source:
            field["source"] = self.source

        field.update({"type": "graphviz_dot", "options": options})


        return field
