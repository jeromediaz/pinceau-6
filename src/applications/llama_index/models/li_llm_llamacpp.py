from typing import TYPE_CHECKING, Any, Optional, List, Dict, cast

from llama_index.core import BasePromptTemplate
from llama_index.core.constants import (
    DEFAULT_TEMPERATURE,
    DEFAULT_NUM_OUTPUTS,
    DEFAULT_CONTEXT_WINDOW,
)
from llama_index.core.llms import LLM
from llama_index.llms.llama_cpp import LlamaCPP
from pydantic import BaseModel

from applications.llama_index.models.li_llm import LiLlm, PredictFn
from core.models.types import ModelUsageMode

if TYPE_CHECKING:
    from llama_index.core.llms.utils import LLMType


class LlamaCppPredictor(BaseModel):
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    llm: LLM

    def predict(
        self,
        prompt: BasePromptTemplate,
        **prompt_args: Any,
    ) -> str:
        """Predict."""

        llama_cpp_llm = cast(LlamaCPP, self.llm)

        llama_cpp_llm._log_template_data(prompt, **prompt_args)

        default_generate_kwargs = llama_cpp_llm.generate_kwargs.copy()

        if self.stop is not None:
            llama_cpp_llm.generate_kwargs["stop"] = self.stop
        if self.max_tokens is not None:
            llama_cpp_llm.generate_kwargs["max_tokens"] = self.max_tokens
        if self.temperature is not None:
            llama_cpp_llm.generate_kwargs["temperature"] = self.temperature

        if self.llm.metadata.is_chat_model:
            messages = llama_cpp_llm._get_messages(prompt, **prompt_args)
            chat_response = llama_cpp_llm.chat(messages)
            output = chat_response.message.content or ""
        else:
            formatted_prompt = llama_cpp_llm._get_prompt(prompt, **prompt_args)
            response = self.llm.complete(formatted_prompt, formatted=True)
            output = response.text

        llama_cpp_llm.generate_kwargs.clear()
        llama_cpp_llm.generate_kwargs.update(default_generate_kwargs)

        return llama_cpp_llm._parse_output(output)

    def __enter__(self) -> PredictFn:
        return self.predict

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class LiLlmLlamacpp(LiLlm):
    META_MODEL = "llamaindex_llm_llama_cpp"

    @property
    def meta_label(self):
        return f"LI - LlamaCPP - {self.others.get('label')}"

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        super_fields = LiLlm.ui_model_fields()
        return [
            *super_fields,
            {"source": "model_path", "type": "text", "opts": ["fullWidth"]},
            {"source": "model_kwargs", "type": "text", "opts": ["fullWidth"]},
            {"source": "generate_kwargs", "type": "text", "opts": ["fullWidth"]},
            {
                "source": "temperature",
                "type": "float",
                "optional": True,
                "defaultValue": DEFAULT_TEMPERATURE,
            },
            {
                "source": "max_new_tokens",
                "type": "int",
                "optional": True,
                "defaultValue": DEFAULT_NUM_OUTPUTS,
            },
            {
                "source": "context_window",
                "type": "int",
                "optional": True,
                "defaultValue": DEFAULT_CONTEXT_WINDOW,
            },
        ]

    def build_llm(self) -> "LLMType":

        allowed_parameters = {
            "model_path",
            "model_kwargs",
            "generate_kwargs",
            "max_new_tokens",
            "context_window",
        }

        params = {}

        for param_name in allowed_parameters:
            param_value = self.others.get(param_name)

            if param_value is not None:
                params[param_name] = param_value

        if "model_kwargs" in params:
            import json

            model_kwargs = params.pop("model_kwargs")
            model_kwargs_dict = json.loads(model_kwargs)
            params["model_kwargs"] = model_kwargs_dict

        if "generate_kwargs" in params:
            import json

            model_kwargs = params.pop("generate_kwargs")
            model_kwargs_dict = json.loads(model_kwargs)
            params["generate_kwargs"] = model_kwargs_dict

        return LlamaCPP(**params)

    def predictor(
        self,
        stop: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):

        params: Dict[str, Any] = {}
        if stop is not None:
            params["stop"] = stop
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        if temperature is not None:
            params["temperature"] = temperature

        return LlamaCppPredictor(llm=cast(LlamaCPP, self.build_llm()), **params)
