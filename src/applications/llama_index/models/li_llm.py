from typing import Any, Optional, List, Protocol, Union, Dict, TYPE_CHECKING

from llama_index.core import BasePromptTemplate
from llama_index.core.llms import LLM
from llama_index.core.llms.utils import resolve_llm
from openai._types import NOT_GIVEN, NotGiven
from pydantic import BaseModel

from core.models.a_model import AModel
from core.models.types import ModelUsageMode

if TYPE_CHECKING:
    from llama_index.core.llms.utils import LLMType


class PredictFn(Protocol):
    def __call__(self, prompt: BasePromptTemplate, **prompt_args: Any) -> str: ...


class LlmPredictor(BaseModel):
    stop: Union[Optional[str], List[str]] | NotGiven = NOT_GIVEN
    max_tokens: Optional[int] | NotGiven = NOT_GIVEN
    temperature: Optional[float] | NotGiven = NOT_GIVEN
    llm: LLM

    class Config:
        arbitrary_types_allowed = True

    def predict(
        self,
        prompt: BasePromptTemplate,
        **prompt_args: Any,
    ) -> str:
        """Predict."""

        self.llm._log_template_data(prompt, **prompt_args)

        if self.llm.metadata.is_chat_model:
            messages = self.llm._get_messages(prompt, **prompt_args)
            chat_response = self.llm.chat(
                messages,
                stop=self.stop,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            output = chat_response.message.content or ""
        else:
            formatted_prompt = self.llm._get_prompt(prompt, **prompt_args)
            response = self.llm.complete(
                formatted_prompt,
                formatted=True,
                stop=self.stop,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            output = response.text

        return self.llm._parse_output(output)

    def __enter__(self) -> PredictFn:
        return self.predict

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class LiLlm(AModel):
    META_MODEL = "llamaindex_llm"

    _llm: Optional[LLM] = None

    @property
    def meta_label(self):
        return self.others.get("label", "")

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        return [
            {"source": "label", "type": "text", "defaultValue": "default"},
        ]

    def build_llm(self) -> "LLMType":
        return "default"

    def predictor(
        self,
        stop: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        if not self._llm:
            self._llm = resolve_llm(self.build_llm())

        params: Dict[str, Any] = {}
        if stop is not None:
            params["stop"] = ",".join(stop)
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        if temperature is not None:
            params["temperature"] = temperature

        return LlmPredictor(llm=self._llm, **params)
