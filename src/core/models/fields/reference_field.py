from typing import Optional

from core.models.fields import ModelField, ModelFieldType


class ReferenceField(ModelField):
    def __init__(self, source: str, *args, reference: Optional[str] = None, **kwargs):
        super().__init__(source, ModelFieldType.REFERENCE, *args, **kwargs)

        self.reference = reference

    def as_json_dict(self) -> dict:
        value = super().as_json_dict()

        value["reference"] = self.reference

        return value
