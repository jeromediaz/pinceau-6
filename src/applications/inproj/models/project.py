from typing import List, ClassVar, Set

from pydantic import Field

from applications.inproj.models.project_artefact import ProjectArtefact
from core.models.a_model import AModel
from ui.helper import P6Field, FieldOptions


class Project(AModel):
    META_MODEL = "inproj_project"

    HIDDEN_FIELDS_LIST: ClassVar[Set[str]] = {"artefacts"}

    name: str
    description: str = P6Field(options=FieldOptions.FULL_WIDTH | FieldOptions.MULTILINE)

    artefacts: List[ProjectArtefact] = Field(json_schema_extra={'tabField': 'name'})
