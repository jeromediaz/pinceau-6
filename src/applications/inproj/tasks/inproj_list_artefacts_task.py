from typing import TYPE_CHECKING

from pydantic import BaseModel

from applications.inproj.models.project import Project
from applications.inproj.models.project_artefact import ProjectArtefact
from core.tasks.task import Task
from core.tasks.types import TaskData, TaskDataAsyncIterator

if TYPE_CHECKING:
    from core.context.context import Context


class ListArtefactsTask(Task["ListArtefactsTask.InputModel"]):

    class InputModel(BaseModel):
        project: Project

    class OutputModel(BaseModel):
        project: Project
        artefact: ProjectArtefact

    async def _generator_process(
        self, context: "Context", data_in: TaskData
    ) -> TaskDataAsyncIterator:

        input_data_object = self.input_object(data_in)
        project = input_data_object.project

        for artefact in project.artefacts:
            yield {"project": project, "artefact": artefact}
