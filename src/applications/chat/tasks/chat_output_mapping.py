from typing import Optional, TYPE_CHECKING, cast

from pydantic import BaseModel

from applications.chat.models.a_chat_message import AChatMessage
from core.tasks.task import Task
from core.tasks.task_dag import TaskDAG
from core.tasks.types import TaskData

if TYPE_CHECKING:
    from core.tasks.task_data import TaskDataContract
    from core.context.context import Context


class ChatOutputMapping(Task["ChatOutputMapping.InputModel"]):

    class Parameters(BaseModel):
        output_field: str
        output_type: str

    def provided_outputs(
        self, parent_task_output: Optional["TaskDataContract"] = None
    ) -> "TaskDataContract":
        # final node, no need to have an output, will be passthrough
        return parent_task_output if parent_task_output else TaskDataContract({})

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        from core.context.chat_context import ChatContext
        from core.context.user_context import UserContext

        chat_context = context.cast_as(ChatContext)
        user_context = context.cast_as(UserContext)

        params = cast(ChatOutputMapping.Parameters, self.merge_params(data_in))

        task_dag = cast(TaskDAG, self.dag())

        if params.output_type == "message":
            await chat_context.add_message(
                context, cast(AChatMessage, data_in.get(params.output_field))
            )
        elif params.output_type == "str":
            await chat_context.add_text_message(
                context,
                cast(str, data_in.get(params.output_field)),
                task_dag.variant_id,
                user_context.user_id,
                "left",
            )

        return {**data_in}
