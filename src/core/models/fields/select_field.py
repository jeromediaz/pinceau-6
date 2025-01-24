from collections import OrderedDict
from typing import Tuple, Optional

from core.models.fields import ModelField, ModelFieldType


class SelectField(ModelField):
    def __init__(
        self,
        source: str,
        *args,
        choices: Optional[OrderedDict[str, str]] = None,
        **kwargs
    ):
        super().__init__(source, ModelFieldType.SELECT, *args, **kwargs)

        self.choices: OrderedDict[str, str] = choices if choices else OrderedDict()

    def as_json_dict(self) -> dict:
        value = super().as_json_dict()

        value["choices"] = list(
            map(lambda item: {"id": item[0], "name": item[1]}, self.choices.items())
        )

        return value

    @classmethod
    def from_list_choices(cls, source: str, *args, choices: list[str], **kwargs):
        new_choices_dict = OrderedDict()
        for choice in choices:
            new_choices_dict[choice] = choice

        cls(source, *args, choices=new_choices_dict, **kwargs)

    @classmethod
    def from_tuple_choices(
        cls, source: str, *args, choices: list[Tuple[str, str]], **kwargs
    ):
        new_choices_dict = OrderedDict()
        for choice in choices:
            new_choices_dict[choice[0]] = choice[1]

        cls(source, *args, choices=new_choices_dict, **kwargs)
