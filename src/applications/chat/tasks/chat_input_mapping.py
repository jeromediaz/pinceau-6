from typing import Optional, TYPE_CHECKING, cast

from pydantic import BaseModel

from applications.chat.models.a_chat_message import AChatMessage, MessageStatus
from core.tasks.task import Task
from core.tasks.types import TaskData

if TYPE_CHECKING:
    from core.tasks.task_data import TaskDataContract
    from core.context.context import Context


class ChatInputMapping(Task["ChatInputMapping.InputModel"]):

    class InputModel(BaseModel):
        message: str

    class Parameters(BaseModel):
        input_field: str
        input_type: str

    def provided_outputs(
        self, parent_task_output: Optional["TaskDataContract"] = None
    ) -> "TaskDataContract":
        outputs = {}

        params = cast(ChatInputMapping.Parameters, self.merge_params({}))
        output_type: type
        if params.input_type == "message":
            output_type = AChatMessage
        else:
            output_type = str

        outputs[params.input_field] = output_type

        from core.tasks.task_data import TaskDataContract

        self_contract = TaskDataContract(outputs)
        if parent_task_output and self.is_passthrough:
            cpy = parent_task_output.copy()
            cpy.add_all(self_contract)
            return cpy

        return self_contract

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        data_input_object = self.input_object(data_in)
        params = cast(ChatInputMapping.Parameters, self.merge_params(data_in))

        from core.context.chat_context import ChatContext

        chat_context = context.cast_as(ChatContext)
        last_message = chat_context.last_message

        if last_message:
            last_message.status = MessageStatus.READ
            await chat_context.update_message(context, last_message)

        if params.input_type == "message":
            return {params.input_field: last_message}
        elif params.input_type == "str":
            return {params.input_field: data_input_object.message}

        return {}
