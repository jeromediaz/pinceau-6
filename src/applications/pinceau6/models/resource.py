from enum import Enum
from typing import List

from core.models.a_model import AModel
from ui.helper import P6Field


class ProviderEnum(str, Enum):
    mongodb = "mongodb"
    elastic = "elastic"


class Resource(AModel):
    META_MODEL = "resource"

    label: str
    name: str
    provider: ProviderEnum = ProviderEnum.mongodb
    tags: List[str] = []
    left_icon: str = P6Field(
        "list-outlined",
        title="Left Icon",
        alias="leftIcon",
        serialization_alias="leftIcon",
    )
