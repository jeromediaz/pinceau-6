import inspect
from typing import Set

from pydantic import BaseModel

from core.models.types import ModelUsageMode


class ExtendedBaseModel(BaseModel):

    @classmethod
    def hidden_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> Set[str]:
        cls_hidden_fields = (
            set(getattr(cls, "HIDDEN_FIELDS"))
            if hasattr(cls, "HIDDEN_FIELDS")
            else set()
        )

        if display_mode != ModelUsageMode.DEFAULT:
            second_field = f"HIDDEN_FIELDS_{display_mode.name}"

            second_cls_fields = (
                getattr(cls, second_field) if hasattr(cls, second_field) else set()
            )
            cls_hidden_fields |= second_cls_fields

        parent_class = cls.__base__

        if not inspect.isclass(parent_class):
            return cls_hidden_fields

        if not hasattr(parent_class, "hidden_fields"):
            return cls_hidden_fields

        final = cls_hidden_fields | parent_class.hidden_fields(
            display_mode=display_mode
        )

        return final
