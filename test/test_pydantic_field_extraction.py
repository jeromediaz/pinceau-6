from typing import Set, List

from pydantic import BaseModel

from misc.pydantic_helper import extract_main_type


def test_simple_type():
    class TestModel(BaseModel):
        string: str
        floating_point: float
        integer: int

    model_fields = TestModel.model_fields

    list_field_info = model_fields['list_field']
    set_field_info = model_fields['set_field']

def test_list_detection_simple_type():

    class TestModel(BaseModel):
        list_field: List[str]
        set_field: Set[str]


    model_fields = TestModel.model_fields

    list_field_info = model_fields['list_field']
    set_field_info = model_fields['set_field']

    print(list_field_info)
    print(set_field_info)

    list_type, is_list_multiple = extract_main_type(list_field_info.annotation)
    set_type, is_set_multiple = extract_main_type(set_field_info.annotation)

    print(list_type)
    print(set_type)

    assert list_type is str
    assert is_list_multiple is True

    assert set_type is str
    assert is_set_multiple is True