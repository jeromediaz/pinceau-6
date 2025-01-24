from typing import TYPE_CHECKING

from pydantic import BaseModel

from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context
    from core.tasks.types import TaskData
    from transformers.pipelines import Pipeline


class PrepareTextClassificationPipelineTask(
    Task["PrepareTextClassificationPipelineTask.InputModel"]
):

    class InputModel(BaseModel):
        pretrained_model: str

    class OutputModel(BaseModel):
        pipeline: "Pipeline"

    async def _process(self, context: "Context", data_in: "TaskData") -> "TaskData":
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            pipeline,
        )
        import torch

        device: int | str = -1
        if torch.cuda.is_available():
            device = 0
        elif torch.backends.mps.is_available():
            device = "mps"

        data_object = self.input_object(data_in)

        tokenizer = AutoTokenizer.from_pretrained(data_object.pretrained_model)
        pretrained_model = AutoModelForSequenceClassification.from_pretrained(
            data_object.pretrained_model
        )

        pipe = pipeline(
            "text-classification",
            model=pretrained_model,
            tokenizer=tokenizer,
            device=device,
        )

        return {"pipeline": pipe}
