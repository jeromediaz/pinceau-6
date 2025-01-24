from typing import Optional, List, cast, Mapping, Any, TYPE_CHECKING

from llama_index.core import PromptTemplate
from pydantic import BaseModel

from applications.llama_index.models.li_llm import LiLlm
from applications.llama_index.tasks.li_llm_predict import LLMPredictTask
from core.context.chat_context import ChatContext
from core.context.composite_context import CompositeContext
from core.context.user_context import UserContext
from core.tasks.task import Task
from core.tasks.task_data import TaskDataContract
from ui.helper import P6Field, FieldOptions

if TYPE_CHECKING:
    from core.context.context import Context

class CondenseChatListTask(Task):

    class Parameters(BaseModel):
        prompt: str = P6Field(
            "", options=FieldOptions.MULTILINE | FieldOptions.FULL_WIDTH
        )

        stop: Optional[List[str]] = None
        max_tokens: Optional[int] = None
        token_limit: Optional[int] = P6Field(ge=0)
        temperature: Optional[float] = None

        input_name: str = "question"
        history_name:str = "history_str"
        output_name: str = "response"


    def provided_outputs(
        self, parent_task_output: Optional["TaskDataContract"] = None
    ) -> "TaskDataContract":
        from core.tasks.task_data import TaskDataContract

        params = cast(LLMPredictTask.Parameters, self.merge_params({}))

        outputs = {params.output_name: str}

        return TaskDataContract(outputs)

    class InputModel(BaseModel):
        class Config:
            arbitrary_types_allowed = True

        llm_model: LiLlm

    def required_inputs(self) -> "TaskDataContract":
        from core.tasks.task_data import TaskDataContract

        dependencies = {}

        params = cast(CondenseChatListTask.Parameters, self.merge_params({}))

        prompt = self.prompt
        if prompt:
            for template_var in prompt.template_vars:
                dependencies[template_var] = {
                    "type": str,
                    "opts": ["multiline", "fullWidth"],
                }

        if params.input_name not in dependencies:
            dependencies[params.input_name] = {
                    "type": str,
                    "opts": ["multiline", "fullWidth"],
                }

        return TaskDataContract(dependencies)


    def __init__(self, prompt: str | PromptTemplate | None = None, **kwargs) -> None:
        if prompt is None:
            self._prompt = None
        else:
            self._prompt = (
                PromptTemplate(template=prompt) if isinstance(prompt, str) else prompt
            )

        super().__init__(**kwargs)

        if self._prompt:
            self._params["prompt"] = self._prompt.template

    @property
    def prompt(self) -> PromptTemplate | None:
        raw_prompt = self.params.get("prompt", None)
        if raw_prompt is None:
            return None

        return (
            PromptTemplate(template=raw_prompt)
            if isinstance(raw_prompt, str)
            else raw_prompt
        )

    def serialize(self) -> Mapping[str, Any]:
        prompt = self._prompt

        serialized_value = {**super().serialize()}

        if prompt is not None:
            serialized_value["prompt"] = prompt.template

        return serialized_value

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> "LLMPredictTask":
        meta = data["_meta"]
        task_id = meta["id"]
        prompt = data.get("prompt")

        params = data["_params"]
        if "prompt" in params:
            prompt = params.pop("prompt")

        return cls(prompt, id=task_id, **params)

    def clone(self, **kwargs) -> "Task":
        other_params = {}
        if "id" in kwargs and "id" in self.params:
            other_params["id"] = kwargs.pop("id")

        return self.__class__(**self._params, **kwargs)


    async def _process(
        self, context: "Context", input_data: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        if not isinstance(context, CompositeContext):
            raise ValueError(
                f"{self.__class__.__name__} context should be a CompositeContext"
            )

        # ici
        dag_ = self.dag()
        if not dag_:
            raise RuntimeError("Must run inside DAG")

        input_model = self.input_object(input_data)
        params_object = cast(LLMPredictTask.Parameters, self.merge_params(input_data))

        variant = dag_.variant_id
        user_context = context.cast_as(UserContext)
        chat_context = context.cast_as(ChatContext)

        chat_history = chat_context.extract_chat_history(user_context.user_id, variant)

        if not chat_history:
            # if no chat history we return the input query as the output
            return {params_object.output_name: input_data.get(params_object.input_name)}

        raw_token_limit = params_object.token_limit

        from llama_index.core.memory.chat_memory_buffer import ChatMemoryBuffer

        token_limit = raw_token_limit if raw_token_limit else None

        memory_buffer = ChatMemoryBuffer.from_defaults(
            chat_history=input_model.chat_history,
            llm=input_model.llm_model._llm,
            token_limit=token_limit,
        )

        prompt = self.prompt
        if prompt is None:
            raise ValueError("Prompt was not provided")

        prompt_args = {var: input_data.get(var) for var in prompt.template_vars}

        prompt_args[params_object.history_name] = memory_buffer.get()

        data_input_object = self.input_object(input_data)
        params_object = cast(LLMPredictTask.Parameters, self.merge_params(input_data))

        with data_input_object.llm_model.predictor(
            stop=params_object.stop,
            max_tokens=params_object.max_tokens,
            temperature=params_object.temperature,
        ) as predict:
            try:
                answer = predict(prompt, **prompt_args)
            except Exception as e:
                answer = f"error {e}"

        return {params_object.output_name: answer}
