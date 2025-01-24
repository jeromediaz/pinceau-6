from enum import Enum
from typing import List, Set, ClassVar

from applications.inproj.models.dependency import Dependency
from core.models.extended_base_model import ExtendedBaseModel


class LockFileType(str, Enum):
    POETRY = "POETRY"
    YARN = "YARN"


class LockFile(ExtendedBaseModel):
    HIDDEN_FIELDS_CREATE: ClassVar[Set[str]] = {"dependencies"}
    HIDDEN_FIELDS_EDIT: ClassVar[Set[str]] = {"dependencies"}

    type: LockFileType
    path: str

    dependencies: List[Dependency] = []
