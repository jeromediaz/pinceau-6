from collections import OrderedDict
from typing import Mapping, Any, Optional, TYPE_CHECKING, Dict

from pydantic import Field

from core.models.types import ModelUsageMode
from core.tasks.task_data import KeyContract
from ui.field_group import FieldGroup

if TYPE_CHECKING:
    from core.tasks.task import Task


class TabField(FieldGroup):

    class Config:
        arbitrary_types_allowed = True

    fields: Dict[str, KeyContract] = OrderedDict()

    def as_ui_field(self, *, for_task: Optional["Task"] = None) -> Mapping[str, Any]:

        field_values = []
        for field_id, contract in self.fields.items():
            field_dict = contract.as_ui_field_def(for_task=for_task, display_mode=ModelUsageMode.DEFAULT)

            source = field_dict.get("source", field_id)
            if source is not False:
                if for_task:
                    source = f"{for_task.full_id}::{source}"
                field_dict["source"] = source
            else:
                del field_dict["source"]

            field_values.append(field_dict)

        return {"source": False, "type": "tab", "fields": field_values}

    @classmethod
    def pydantic(cls, *, title: str) -> Any:
        return Field(TabField(), title=title)
