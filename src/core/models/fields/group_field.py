from core.models.fields import ModelField, ModelFieldType


class GroupField(ModelField):
    def __init__(self, source: str, *args, fields: list[ModelField], **kwargs):
        super().__init__(source, ModelFieldType.REFERENCE, *args, **kwargs)

        self.fields = fields

    def as_json_dict(self) -> dict:
        value = super().as_json_dict()

        value["fields"] = list(map(lambda field: field.as_json_dict(), self.fields))

        return value
