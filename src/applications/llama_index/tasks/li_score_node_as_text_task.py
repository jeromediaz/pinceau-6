from typing import List, TYPE_CHECKING, cast, Mapping, Any

from llama_index.core.schema import NodeWithScore
from pydantic import BaseModel

from core.context.chat_context import ChatContext
from core.tasks.task import Task
from core.tasks.task_dag import TaskDAG
from core.tasks.types import TaskData, TaskDataAsyncIterator

if TYPE_CHECKING:
    from core.context.context import Context


class LiScoreNodeAsTextTask(Task["LiScoreNodeAsTextTask.InputModel"]):

    class InputModel(BaseModel):
        results: List[NodeWithScore]

    class OutputModel(BaseModel):
        results: str

    async def _generator_process(
        self, context: "Context", data_in: TaskData
    ) -> TaskDataAsyncIterator:
        data_input_object = self.input_object(data_in)

        for result in data_input_object.results:
            yield {"results": str(result)}


class PassthroughTask(Task["PassthroughTask.InputModel"]):

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("is_passthrough", True)
        super().__init__(*args, **kwargs)

    class Parameters(BaseModel):
        log_value: str

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        parameter_object = cast(
            PassthroughTask.Parameters, self.merge_params(data_input)
        )

        task_dag = cast(TaskDAG, self.dag())

        if parameter_object.log_value:
            the_value = data_input.get(parameter_object.log_value)
            if the_value and isinstance(the_value, str):
                chat_context = context.cast_as(ChatContext)
                if chat_context:
                    await chat_context.add_system_message(
                        context,
                        f"{parameter_object.log_value}: {the_value}",
                        task_dag.variant_id,
                    )

        return data_input
