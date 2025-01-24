import copy
import datetime
import inspect
import typing
from collections import OrderedDict
from enum import Enum
from typing import Any, Optional, Type, Tuple, Mapping, Dict

from pydantic.fields import FieldInfo, ComputedFieldInfo

from core.models.types import ModelUsageMode
from core.tasks.task import Task
from misc.pydantic_helper import extract_type_origin, extract_computed_type_origin
from ui.fieldable import Fieldable


class KeyContract:
    def __init__(
        self,
        type_: Type | Tuple[str, Type],
        optional: bool = False,
        multiple=False,
        default=None,
        field_info: Optional[FieldInfo] = None,
        computed_field_info: Optional[ComputedFieldInfo] = None,
        **kwargs,
    ):
        self.type: Type = type_[1] if isinstance(type_, tuple) else type_
        self.optional: bool = optional
        self._is_multiple: bool = multiple
        self.other = kwargs
        self.default = default
        self._field_info: Optional[FieldInfo] = field_info
        self._computed_field_info: Optional[ComputedFieldInfo] = computed_field_info
        self._label = field_info.title if field_info else kwargs.get("label", None)
        if isinstance(type_, tuple):
            self.other["type"] = type_[0]

    @classmethod
    def from_field(cls, field_info: FieldInfo) -> "KeyContract":
        main_type, optional, multiple, default = extract_type_origin(field_info)

        return cls(
            main_type,
            optional=optional,
            multiple=multiple,
            default=default,
            field_info=field_info,
        )

    @classmethod
    def from_computed_field(cls, field_info: ComputedFieldInfo) -> "KeyContract":
        main_type, optional, multiple, default = extract_computed_type_origin(
            field_info
        )

        return cls(
            main_type,
            optional=optional,
            multiple=multiple,
            default=default,
            computed_field_info=field_info,
        )

    @classmethod
    def from_default(
        cls, type_: Type, optional: bool = False, multiple: bool = False, **kwargs
    ) -> "KeyContract":
        return cls(type_, optional=optional, multiple=multiple)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyContract":
        copy_value: Dict[str, Any] = copy.deepcopy(data)
        type_value = copy_value.pop("type")
        optional = copy_value.pop("optional", False)
        multiple = copy_value.pop("multiple", False)
        default = copy_value.pop("defaultValue", None)

        return cls(
            type_=type_value, optional=optional, multiple=multiple, default=default
        )

    def is_matched_by(self, value: Any) -> bool:
        if not value:
            return not self.optional

        return isinstance(value, self.type)

    def copy(self) -> "KeyContract":
        return KeyContract(self.type, self.optional)

    def is_compatible(self, contract: "KeyContract") -> bool:
        if self.type != contract.type or not issubclass(contract.type, self.type):
            return False
        if self.optional and not contract.optional:
            return False

        return True

    def update(self, contract: "KeyContract") -> bool:
        if not self.is_compatible(contract):
            return False

        self.optional = self.optional and contract.optional
        self.type = contract.type

        return True

    def wrapped_in(self) -> Optional[str]:
        if self._field_info is not None and self._field_info.json_schema_extra:
            json_schema_extra = self._field_info.json_schema_extra
            if json_schema_extra is None:
                return None
            if callable(json_schema_extra):
                # not handled
                extra = {}
            else:
                extra = json_schema_extra

            return typing.cast(Optional[str], extra.get("wrapped_in", None))
        return None

    def as_ui_field_def(
        self, *, for_task: Optional["Task"] = None, display_mode=ModelUsageMode.DEFAULT
    ):

        dict_representation = {**self.other}

        if self._label:
            dict_representation["label"] = self._label

        from core.models.a_model import AModel
        from pydantic import BaseModel

        if inspect.isclass(self.type):
            if issubclass(self.type, AModel):
                dict_representation["type"] = "model"
                model = self.type.META_MODEL
                dict_representation["model"] = model

            elif issubclass(self.type, Fieldable) and self.default is not None:
                dict_representation.update(self.default.as_ui_field(for_task=for_task))
                return dict_representation

            elif issubclass(self.type, BaseModel):
                from ui.helper import ui_fields_from_base_model

                dict_representation["type"] = "group"
                dict_representation["fields"] = ui_fields_from_base_model(
                    self.type, display_mode=display_mode
                )

            elif issubclass(self.type, Enum):
                dict_representation["type"] = "select"
                dict_representation["choices"] = [
                    {"id": case.value, "name": case.value} for case in self.type
                ]

                if self.default is not None:
                    dict_representation["defaultValue"] = self.default.name



        if "type" not in dict_representation:
            type_name = self.type.__name__.lower()

            if type_name == "str":
                type_name = "text"
            dict_representation["type"] = type_name

        if self.optional:
            dict_representation["optional"] = self.optional

        # TODO: a computed field should be disabled!

        if self._computed_field_info:
            # computed_fields are always disabled
            opts: typing.List[str] = dict_representation.setdefault("opts", [])
            opts.append("disabled")

        if self._field_info is not None:
            validations: Dict[str, str | int | float | Mapping[str, str]] = {}

            for metadata in self._field_info.metadata:
                metadata_class_name_lower = metadata.__class__.__name__.lower()
                if metadata_class_name_lower in {"ge", "gt", "le", "lt"}:
                    filter_value = getattr(metadata, metadata_class_name_lower)

                    if isinstance(filter_value, (str, int, float)):
                        validations[metadata_class_name_lower] = filter_value

                    if isinstance(
                        filter_value, (datetime.datetime, datetime.time, datetime.date)
                    ):
                        key = filter_value.__class__.__name__
                        validations[key] = filter_value.isoformat()

                if metadata_class_name_lower in {"maxlen", "minlen"}:
                    attribute_name = metadata_class_name_lower[:3] + "_length"
                    validation_key = metadata_class_name_lower[:3] + "Length"
                    length_value = getattr(metadata, attribute_name)
                    validations[validation_key] = length_value

            if validations:
                dict_representation["validations"] = validations

        if self.default is not None and not isinstance(self.default, property):
            default_value = self.default

            if isinstance(
                default_value,
                (datetime.date, datetime.time, datetime.datetime),
            ):
                default_value = default_value.isoformat()
            elif isinstance(default_value, datetime.timedelta):
                default_value = str(default_value)

            dict_representation["defaultValue"] = default_value

        if self._is_multiple:
            dict_representation["multiple"] = True

        if self._field_info is not None:
            json_schema_extra = self._field_info.json_schema_extra

            if json_schema_extra and isinstance(json_schema_extra, dict):

                # json_schema_extra.pop("wrapped_in", None)
                dict_representation.update(json_schema_extra)
                if "wrapped_in" in dict_representation:
                    del dict_representation["wrapped_in"]

        return dict_representation

    def __str__(self):
        return f"({self.type} optional: {self.optional})"

    def pydantic_field(self) -> tuple[type, Optional[FieldInfo]]:
        return self.type, None if self.optional else FieldInfo()


class TaskDataContract:
    def __init__(self, data: Optional[Mapping[str, Any]] = None) -> None:
        self.contract_dict: Dict[str, KeyContract] = OrderedDict()

        if data is None:
            data = {}

        for key, value in data.items():
            if isinstance(value, type):
                key_contract = KeyContract.from_default(value)
            elif isinstance(value, tuple):
                key_contract = KeyContract(value[0], value[1])
            elif isinstance(value, dict):
                copy_value = copy.deepcopy(value)
                type_value = copy_value.pop("type")
                optional = copy_value.pop("optional", False)
                key_contract = KeyContract(type_value, optional, **copy_value)
            elif isinstance(value, FieldInfo):
                key_contract = KeyContract.from_field(value)
            elif isinstance(value, ComputedFieldInfo):
                key_contract = KeyContract.from_computed_field(value)
            else:
                continue

            self.contract_dict[key] = key_contract

    def __str__(self):
        values = [
            f"{key} : {value_contract}"
            for key, value_contract in self.contract_dict.items()
        ]

        return " , ".join(values)

    def add(self, key: str, contract: "KeyContract") -> bool:
        if key in self.contract_dict:
            if not self.contract_dict[key].update(contract):
                return False

        self.contract_dict[key] = contract

        return True

    def add_all(self, contract: "TaskDataContract") -> bool:
        for key, data_contract in contract.contract_dict.items():
            if not self.add(key, data_contract):
                return False

        return True

    def subtract_all(self, contract: "TaskDataContract") -> bool:
        for key, data_contract in contract.contract_dict.items():
            if key not in self.contract_dict:
                continue

            local_contract = self.contract_dict[key]
            if not data_contract.is_compatible(local_contract):
                return False

            self.contract_dict.pop(key)

        return True

    def copy(self) -> "TaskDataContract":
        new_contract = TaskDataContract({})

        for key, contract in self.contract_dict.items():
            new_contract.add(key, contract.copy())

        return new_contract

    def fields_map(
        self, *, for_task: Optional["Task"] = None, display_mode=ModelUsageMode.DEFAULT
    ) -> Mapping[str, Mapping[str, Any]]:
        wrapped_contract: Dict[str, KeyContract] = OrderedDict()
        wrapped_fields: Dict[str, KeyContract] = {}
        for key, contract in self.contract_dict.items():
            wrapped_in = contract.wrapped_in()
            if wrapped_in:
                wrapper_contract = (
                    wrapped_contract[wrapped_in]
                    if wrapped_in in wrapped_contract
                    else wrapped_fields[wrapped_in]
                )
                wrapper_contract.default.fields[key] = contract
                wrapped_fields[key] = contract
            else:
                wrapped_contract[key] = contract

        result_dict = OrderedDict()
        for key, contract in wrapped_contract.items():
            result_dict[key] = contract.as_ui_field_def(for_task=for_task, display_mode=display_mode)

        return result_dict

    def pydantic_fields(self) -> Mapping[str, tuple[type, FieldInfo]]:
        result_dict: Dict[str, tuple[type, FieldInfo]] = dict()
        for key, contract in self.contract_dict.items():
            pydantic_field = contract.pydantic_field()

            if (
                pydantic_field and pydantic_field[1]
            ):  # we need to check we have the FieldInfo
                result_dict[key] = typing.cast(Tuple[type, FieldInfo], pydantic_field)

        return typing.cast(Mapping[str, tuple[type, FieldInfo]], result_dict)
