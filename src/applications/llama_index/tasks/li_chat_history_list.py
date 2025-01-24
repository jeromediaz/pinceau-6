from typing import Mapping, Any, TYPE_CHECKING, cast, List, Optional

from llama_index.core.base.llms.generic_utils import messages_to_history_str
from llama_index.core.base.llms.types import ChatMessage
from pydantic import BaseModel, Field

from applications.llama_index.models.li_llm import LiLlm
from core.context.chat_context import ChatContext
from core.context.user_context import UserContext
from core.tasks.task import Task
from core.tasks.task_data import TaskDataContract

if TYPE_CHECKING:
    from core.context.context import Context


class ChatListTask(Task["ChatListTask.InputModel"]):

    class OutputModel(BaseModel):
        chat_history: List[ChatMessage]

    async def _process(
        self, context: "Context", input_data: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        dag_ = self.dag()
        if not dag_:
            raise RuntimeError("Must run inside DAG")

        variant = dag_.variant_id
        user_context = context.cast_as(UserContext)
        chat_context = context.cast_as(ChatContext)

        chat_history = chat_context.extract_chat_history(user_context.user_id, variant)

        return {"chat_history": chat_history}


class ChatBufferListTask(Task["ChatBufferListTask.InputModel"]):

    class Parameters(BaseModel):
        token_limit: Optional[int] = Field(ge=0)

    class InputModel(BaseModel):
        class Config:
            arbitrary_types_allowed = True

        chat_history: List[ChatMessage]
        llm_model: LiLlm

    class OutputModel(BaseModel):
        chat_history: List[ChatMessage]

    async def _process(
        self, context: "Context", input_data: Mapping[str, Any]
    ) -> Mapping[str, Any]:

        input_model = self.input_object(input_data)
        parameters = cast(ChatBufferListTask.Parameters, self.merge_params(input_data))
        raw_token_limit = parameters.token_limit

        from llama_index.core.memory.chat_memory_buffer import ChatMemoryBuffer

        token_limit = raw_token_limit if raw_token_limit else None

        memory_buffer = ChatMemoryBuffer.from_defaults(
            chat_history=input_model.chat_history,
            llm=input_model.llm_model._llm,
            token_limit=token_limit,
        )

        return {"chat_history": memory_buffer.get()}


class ChatHistoryStringTask(Task["ChatHistoryStringTask.InputModel"]):

    class InputModel(BaseModel):
        chat_history: List[ChatMessage]

    class OutputModel(BaseModel):
        history_str: str

    class Parameters(BaseModel):
        output_name: str = "history_str"

    def provided_outputs(
        self, parent_task_output: Optional["TaskDataContract"] = None
    ) -> "TaskDataContract":
        from core.tasks.task_data import TaskDataContract

        params = cast(ChatHistoryStringTask.Parameters, self.merge_params({}))

        outputs = {params.output_name: str}

        return TaskDataContract(outputs)

    async def _process(
        self, context: "Context", input_data: Mapping[str, Any]
    ) -> Mapping[str, Any]:

        input_model = self.input_object(input_data)
        params = cast(ChatHistoryStringTask.Parameters, self.merge_params(input_data))

        return {params.output_name: messages_to_history_str(input_model.chat_history)}
