from collections import OrderedDict
from typing import Dict, Mapping, Any, Optional, TYPE_CHECKING

from core.models.types import ModelUsageMode
from core.tasks.task_data import KeyContract
from ui.fieldable import Fieldable

if TYPE_CHECKING:
    from core.tasks.task import Task


class FieldGrid(Fieldable):

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

            if "grid" not in field_dict:
                field_dict["grid"] = {"xs": 12, "sm": 6}

            field_values.append(field_dict)

        return {"type": "grid", "fields": field_values, "source": False}
