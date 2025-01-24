from typing import TYPE_CHECKING, Dict, Any

from llama_index.llms.openai import OpenAI

from applications.llama_index.models.li_llm import LiLlm
from core.models.types import ModelUsageMode

if TYPE_CHECKING:
    from llama_index.core.llms.utils import LLMType


class LILLMOPENAI(LiLlm):
    META_MODEL = "llamaindex_llm_openai"

    @property
    def meta_label(self):
        return f"LI - OPENAI - {self.others.get('label')}"

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        super_fields = LiLlm.ui_model_fields()
        return [
            *super_fields,
            {
                "source": "_parameters",
                "type": "select",
                "multiple": True,
                "choices": [
                    {"id": "model::str", "name": "Model (str)"},
                    {"id": "model::list", "name": "Model (list)"},
                    {"id": "temperature", "name": "Temperature"},
                    {"id": "api_key", "name": "API KEY"},
                ],
            },
            {
                "source": "model",
                "type": "text",
                "condition": {"_parameters": {"$include": "model::str"}},
            },
            {
                "source": "model",
                "type": "select",
                "condition": {"_parameters": {"$include": "model::list"}},
                "choices": [
                    {"id": "gpt-4-0125-preview", "name": "gpt-4-0125-preview"},
                    {"id": "gpt-4-0613", "name": "gpt-4-0613"},
                    {"id": "gpt-3.5-turbo-0125", "name": "gpt-3.5-turbo-0125"},
                    {"id": "gpt-3.5-turbo-1106", "name": "gpt-3.5-turbo-1106"},
                ],
            },
            {
                "source": "temperature",
                "type": "float",
                "condition": {"_parameters": {"$include": "temperature"}},
            },
            {
                "source": "api_key",
                "type": "text",
                "opts": ["fullWidth"],
                "condition": {"_parameters": {"$include": "api_key"}},
            },
        ]

    def build_llm(self) -> "LLMType":

        params: Dict[str, Any] = dict()

        parameters = self.others.get("parameters", [])
        for parameter_name in parameters:
            parameter_start = parameter_name.split("::")[0]

            if parameter_start in self.others:
                params[parameter_start] = self.others.get(parameter_start)

        return OpenAI(**params)
