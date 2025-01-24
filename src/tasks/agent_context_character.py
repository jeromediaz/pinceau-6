import copy
from typing import cast, Mapping, Any, Dict, Tuple, Type

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from core.tasks.task import Task
from tasks.logged_alpaca_llm_task import LoggedAlpacaLlmTask


class AgentContextCharacter(Task):
    class InputModel(BaseModel):
        event: str
        character: str
        character_name: str
        character_description: str

    class OutputModel(BaseModel):
        instruction: str
        end_word: str

    def input_object(
        self, data: Mapping[str, Any]
    ) -> "AgentContextCharacter.InputModel":
        model_fields = copy.deepcopy(self.__class__.InputModel.model_fields)

        character = data.get("character")
        if character and isinstance(character, str):
            model_fields["character_name"].validation_alias = f"{character}_name"
            model_fields["character_description"].validation_alias = (
                f"{character}_description"
            )

        dynamic_model_fields: Dict[str, Tuple[type[Any] | None, FieldInfo]] = dict()
        for field_key, field_info in model_fields.items():
            dynamic_model_fields[field_key] = (field_info.annotation, field_info)

        input_model = cast(
            Type[AgentContextCharacter.InputModel],
            create_model("InputModelDynamic", **dynamic_model_fields),  # type: ignore
        )

        return input_model.model_validate(data)

    async def _process(
        self, context, input_data: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        input_model_object = self.input_object(input_data)

        character_name = input_model_object.character_name
        character_description = input_model_object.character_description
        event = input_model_object.event

        instruction = f"{character_description}n\nRemove from {character_name}'s character description elements non relevant considering the given situation, do not add elements."

        llm_task = LoggedAlpacaLlmTask()

        llm_task_input = {
            "instruction": instruction,
            "input": event,
        }

        llm_task_output = cast(
            Mapping[str, Any], await llm_task.process(context, llm_task_input)
        )
        answer: str = cast(str, llm_task_output["text"])

        return {**input_data, "character_instruction": answer}
