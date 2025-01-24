import types
from typing import Optional, List
from typing import get_origin, get_args, Union

from pydantic import BaseModel


class TestModel(BaseModel):
    string: str
    floating_point: float = 2.0
    string_list: List[str]
    optional_int: Optional[int]


field = TestModel.model_fields["floating_point"]

origin_type = get_origin(field.annotation)

is_list = origin_type is list
is_union = origin_type is Union

if is_union:
    annotation_args = get_args(field.annotation)

    is_optional = annotation_args[-1] is types.NoneType

    print(f"{field.annotation=} Optional: {is_optional}, {annotation_args[0] is int}")

elif is_list:
    annotation_args = get_args(field.annotation)
    print(f"{field.annotation=} list: True, {annotation_args[0] is str}")
else:
    print(f"{field.annotation=} list: False, {origin_type is str}")
