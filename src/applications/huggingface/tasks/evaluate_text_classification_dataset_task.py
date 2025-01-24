from typing import TYPE_CHECKING

from pydantic import BaseModel

from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context
    from core.tasks.types import TaskData
    from transformers.pipelines import Pipeline
    from datasets import Dataset


class EvaluateTextClassificationDatasetTask(
    Task["EvaluateTextClassificationDatasetTask.InputModel"]
):

    class InputModel(BaseModel):
        pipeline: "Pipeline"
        dataset: "Dataset"

    class OutputModel(BaseModel):
        pipeline: "Pipeline"

    async def _process(self, context: "Context", data_in: "TaskData") -> "TaskData":

        data_object = self.input_object(data_in)

        for evaluation in data_object.pipeline(data_object.dataset):
            print(evaluation)
            exit()

        return {**data_in, "results": ""}
