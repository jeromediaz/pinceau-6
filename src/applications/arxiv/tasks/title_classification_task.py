import json
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer

from applications.huggingface.models.training_arguments_model import (
    TrainingArgumentsModel,
)
from applications.huggingface.models.training_label_provider import (
    TrainingLabelProvider,
)
from core.tasks.task import Task
from core.tasks.types import TaskData

if TYPE_CHECKING:
    from core.context.context import Context


class TitleClassificationTask(Task["TitleClassificationTask.InputModel"]):

    class UI(BaseModel):
        results: str = Field(title="Results")

    class InputModel(BaseModel):
        class ClassConfig:
            arbitrary_types_allowed = True

        pretrained_model: str
        arguments: TrainingArgumentsModel
        label_provider: TrainingLabelProvider
        title: str

    class OutputModel(BaseModel):
        result: str

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        try:
            data_object = self.input_object(data_in)

            tokenizer = AutoTokenizer.from_pretrained(data_object.pretrained_model)

            pretrained_model = AutoModelForSequenceClassification.from_pretrained(
                data_object.arguments.output_dir,
            )

            pipe = pipeline(
                "text-classification", model=pretrained_model, tokenizer=tokenizer
            )
            results = pipe(data_object.title)
        except Exception as e:
            print(e)
            results = str(e)

        await context.event(
            self,
            "data",
            {
                "results": json.dumps(results),
            },
        )

        return {"result": results[0]["label"]}
