from enum import Enum
from typing import List

from pydantic import BaseModel

from applications.inproj.models.version_object import VersionObject


class DependencyType(str, Enum):
    NPM = "npm"
    PYTHON = "python"


class Dependency(BaseModel):
    location: str
    name: str
    version: VersionObject
    type: DependencyType

    vulnerabilities: List[str] = []
