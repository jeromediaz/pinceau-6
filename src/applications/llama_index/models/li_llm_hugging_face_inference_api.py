from typing import TYPE_CHECKING, Any, List, Optional, Dict, cast

from llama_index.core import BasePromptTemplate
from llama_index.core.llms import LLM
from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
from pydantic import BaseModel

from applications.llama_index.models.li_llm import LiLlm, PredictFn
from core.models.types import ModelUsageMode

if TYPE_CHECKING:
    from llama_index.core.llms.utils import LLMType


class LlmHuggingFaceInferenceApiPredictor(BaseModel):
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

        self.llm._log_template_data(prompt, **prompt_args)

        if self.llm.metadata.is_chat_model:
            parameters = {}

            if self.temperature is not None:
                parameters["temperature"] = self.temperature
            if self.max_tokens is not None:
                parameters["max_length"] = self.max_tokens

            messages = self.llm._get_messages(prompt, **prompt_args)
            chat_response = self.llm.chat(messages, parameters=parameters)
            output = chat_response.message.content or ""
        else:
            formatted_prompt = self.llm._get_prompt(prompt, **prompt_args)

            params: Dict[str, Any] = {}
            if self.temperature is not None:
                params["temperature"] = self.temperature
            if self.max_tokens is not None:
                params["max_new_tokens"] = self.max_tokens
            if self.stop is not None:
                params["stop_sequences"] = self.stop

            response = self.llm.complete(formatted_prompt, formatted=True, **params)
            output = response.text

        return self.llm._parse_output(output)

    def __enter__(self) -> PredictFn:
        return self.predict

    def __exit__(self, exc_type, exc_val, exc_tb):
        # nothing to do here
        pass


class LiLlmHfInferenceApi(LiLlm):
    META_MODEL = "llamaindex_llm_hugging_face_inference_api"

    @property
    def meta_label(self):
        return f"LI - HF-Inference-API - {self.others.get('label')}"

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        super_fields = LiLlm.ui_model_fields()
        return [
            *super_fields,
            {
                "source": "model_name",
                "type": "text",
            },
            {
                "source": "temperature",
                "type": "float",
                "optional": True,
            },
            {
                "source": "token",
                "type": "text",
                "opts": ["fullWidth"],
                "optional": True,
            },
        ]

    def build_llm(self) -> "LLMType":

        params = dict()

        allowed_parameters = {
            "model_name",
            "temperature",
            "token",
        }

        for param_name in allowed_parameters:
            param_value = self.others.get(param_name)

            if param_value is not None:
                params[param_name] = param_value

        return HuggingFaceInferenceAPI(**params)

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

        return LlmHuggingFaceInferenceApiPredictor(
            llm=cast(HuggingFaceInferenceAPI, self.build_llm()), **params
        )
