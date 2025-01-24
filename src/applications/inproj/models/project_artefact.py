from typing import List

from pydantic import BaseModel, Field

from applications.inproj.models.lock_file import LockFile


class ProjectArtefact(BaseModel):
    name: str = "artefact"
    base_path: str
    lock_files: List[LockFile] = Field(json_schema_extra={'tabField': 'type'})  # TODO: set it as inline
