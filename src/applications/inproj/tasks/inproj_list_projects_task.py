from typing import TYPE_CHECKING

from pydantic import BaseModel

from applications.inproj.models.project import Project
from core.database.mongodb import MongoDBHandler
from core.tasks.task import Task
from core.tasks.types import TaskData, TaskDataAsyncIterator

if TYPE_CHECKING:
    from core.context.context import Context


class ListProjectsTask(Task):

    class OutputModel(BaseModel):
        project: Project

    async def _generator_process(
        self, context: "Context", data_in: TaskData
    ) -> TaskDataAsyncIterator:

        mongodb_handler = MongoDBHandler.from_default(context)

        projects = mongodb_handler.load_multiples("inproj_project", {})

        for project in projects:
            yield {"project": project}
