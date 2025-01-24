from enum import Enum
from typing import List, cast

from core.tasks.types import JSONParam, JSONValue


class ModelFieldType(Enum):
    TEXT = "text"
    URL = "url"
    BOOLEAN = "bool"
    INT = "int"
    FLOAT = "float"
    REFERENCE = "reference"
    TIME = "time"
    DATETIME = "datetime"
    DATE = "date"
    GROUP = "group"
    SELECT = "select"


class HideOn(Enum):
    LIST = "list"


class ModelField:
    def __init__(
        self,
        source: str,
        type_: ModelFieldType,
        *args,
        multiple: bool = False,
        **kwargs
    ):
        self.source = source
        self.type = type_
        self.field_flags = set(args)
        self.field_other_args = kwargs
        self.multiple = multiple

    def as_json_dict(self) -> dict:
        value: JSONParam = {"source": self.source, "type": self.type.value}

        opts: List[str] = []
        if self.multiple:
            value["multiple"] = True

        if "fullWidth" in self.field_flags:
            opts.append("fullWidth")

        if "multiline" in self.field_flags:
            opts.append("multiline")

        if opts:
            value["opts"] = cast(JSONValue, opts)

        if "hideOn" in self.field_other_args:
            value["hideOn"] = [
                val if isinstance(val, str) else val.value
                for val in self.field_other_args.get("hideOn", [])
            ]

        if "render_as" in self.field_other_args:
            value["render"] = self.field_other_args["render_as"]

        return value

    @staticmethod
    def for_text(source: str, *args, **kwargs) -> "ModelField":
        multiple = kwargs.pop("multiple", False)

        return ModelField(
            source, ModelFieldType.TEXT, *args, multiple=multiple, **kwargs
        )
