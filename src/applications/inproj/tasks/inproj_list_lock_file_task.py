from typing import TYPE_CHECKING

from pydantic import BaseModel

from applications.inproj.models.lock_file import LockFile
from applications.inproj.models.project import Project
from applications.inproj.models.project_artefact import ProjectArtefact
from core.tasks.task import Task
from core.tasks.types import TaskData, TaskDataAsyncIterator

if TYPE_CHECKING:
    from core.context.context import Context


class ListLockfileTask(Task["ListLockfileTask.InputModel"]):

    class InputModel(BaseModel):
        project: Project
        artefact: ProjectArtefact

    class OutputModel(BaseModel):
        project: Project
        artefact: ProjectArtefact
        lock_file: LockFile

    async def _generator_process(
        self, context: "Context", data_in: TaskData
    ) -> TaskDataAsyncIterator:

        input_data_object = self.input_object(data_in)
        project = input_data_object.project
        artefact = input_data_object.artefact

        for lock_file in artefact.lock_files:
            yield {"project": project, "artefact": artefact, "lock_file": lock_file}
