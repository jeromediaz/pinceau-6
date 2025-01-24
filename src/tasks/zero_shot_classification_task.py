import json
from typing import Mapping, Any, TYPE_CHECKING

from pydantic import BaseModel, Field
from transformers import pipeline

from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context


class ZeroShotClassificationTask(Task):

    class UI(BaseModel):
        result: str = Field(title="Result")

    class InputModel(BaseModel):
        query: str
        classes: str | list[str]

    class OutputModel(BaseModel):
        classification: dict

    def __init__(self, model: str = "facebook/bart-large-mnli", **kwargs):
        super().__init__(**kwargs)
        self._model = model

    def clone(self, **kwargs) -> "Task":
        return self.__class__(self._model, **self.params, **kwargs)

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        data_input_object = self.input_object(data_input)

        query = data_input_object.query
        classes = data_input_object.classes
        if isinstance(classes, str):
            classes = classes.split(",")

        pipe = pipeline(model=self._model)
        result = pipe(
            query,
            candidate_labels=classes,
        )

        result_as_json = json.dumps(result)
        await context.event(self, "data", {"result": result_as_json})

        return {**data_input, **result}
