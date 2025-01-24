from typing import Optional, Mapping, Any

from pydantic import Field
from transformers import TrainingArguments

from core.models.a_model import AModel
from core.models.types import ModelUsageMode


class TrainingArgumentsModel(AModel):
    META_MODEL = "training_arguments"

    output_dir: str = Field(
        title="output directory",
        description="Where the trained model and check points will be stored",
    )
    learning_rate: float
    per_device_train_batch_size: int
    per_device_eval_batch_size: int
    gradient_accumulation_steps: int = Field(1, ge=1)
    num_train_epochs: int = Field(2, ge=1)
    weight_decay: float = 0.01
    eval_strategy: str
    eval_steps: Optional[int] = Field(None, ge=0)
    eval_accumulation_steps: Optional[int] = Field(None, gt=0)
    save_strategy: str
    save_steps: int = 500
    load_best_model_at_end: bool = False
    logging_strategy: str = "steps"
    logging_first_step: bool = False
    logging_steps: int = 500
    save_total_limit: Optional[int] = None
    save_only_model: bool = False

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:

        return [
            {
                "source": "output_dir",
                "type": "text",
                "label": "output directory",
                "helperText": "Where the trained model and check points will be stored",
            },
            {"source": "learning_rate", "type": "float", "defaultValue": 5e-5},
            {"source": "per_device_train_batch_size", "type": "int", "defaultValue": 8},
            {"source": "per_device_eval_batch_size", "type": "int", "defaultValue": 8},
            {"source": "gradient_accumulation_steps", "type": "int", "defaultValue": 1},
            {"source": "num_train_epochs", "type": "float", "defaultValue": 3.0},
            {"source": "weight_decay", "type": "float", "defaultValue": 0.0},
            {
                "source": "eval_strategy",
                "defaultValue": "no",
                "type": "select",
                "choices": [
                    {"id": "no", "name": "No evaluation"},
                    {"id": "steps", "name": "Every 'eval_steps'"},
                    {"id": "epoch", "name": "At the end of each epoch"},
                ],
            },
            {
                "source": "eval_steps",
                "type": "int",
                "condition": {"eval_strategy": "steps"},
                "helperText": "Number of steps between two evaluations",
            },
            {
                "source": "eval_accumulation_steps",
                "type": "int",
                "optional": True,
                "condition": {"eval_strategy": {"$ne": "no"}},
            },
            {
                "source": "save_strategy",
                "defaultValue": "steps",
                "type": "select",
                "choices": [
                    {"id": "no", "name": "No save"},
                    {"id": "steps", "name": "Every 'save_steps'"},
                    {"id": "epoch", "name": "At the end of each epoch"},
                ],
                "helperText": "When to write check-points",
            },
            {
                "source": "save_steps",
                "type": "int",
                "defaultValue": 500,
                "condition": {"save_strategy": "steps"},
            },
            {"source": "logging_first_step", "type": "bool", "defaultValue": False},
            {
                "source": "logging_strategy",
                "defaultValue": "steps",
                "type": "select",
                "choices": [
                    {"id": "no", "name": "No save"},
                    {"id": "epoch", "name": "At the end of each epoch"},
                    {"id": "steps", "name": "Every 'logging_steps'"},
                ],
                "helperText": "When to log data during training",
            },
            {
                "source": "logging_steps",
                "type": "int",
                "defaultValue": 500,
                "condition": {"logging_strategy": "steps"},
            },
            {"source": "load_best_model_at_end", "type": "bool", "defaultValue": False},
            {"source": "save_total_limit", "type": "int", "optional": True},
            {"source": "save_only_model", "type": "bool", "defaultValue": False},
        ]

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **super().as_dict(**kwargs),
            "output_dir": self.output_dir,
            "learning_rate": self.learning_rate,
            "per_device_train_batch_size": self.per_device_train_batch_size,
            "per_device_eval_batch_size": self.per_device_eval_batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "num_train_epochs": self.num_train_epochs,
            "weight_decay": self.weight_decay,
            "eval_strategy": self.eval_strategy,
            "eval_steps": self.eval_steps,
            "eval_accumulation_steps": self.eval_accumulation_steps,
            "save_strategy": self.save_strategy,
            "save_steps": self.save_steps,
            "logging_first_step": self.logging_first_step,
            "logging_steps": self.logging_steps,
            "load_best_model_at_end": self.load_best_model_at_end,
            "save_total_limit": self.save_total_limit,
            "save_only_model": self.save_only_model

        }

    def as_training_arguments(self) -> TrainingArguments:
        return TrainingArguments(
            output_dir=self.output_dir,
            learning_rate=self.learning_rate,
            per_device_train_batch_size=self.per_device_train_batch_size,
            per_device_eval_batch_size=self.per_device_eval_batch_size,
            gradient_accumulation_steps=self.gradient_accumulation_steps,
            num_train_epochs=self.num_train_epochs,
            weight_decay=self.weight_decay,
            eval_strategy=self.eval_strategy,
            eval_steps=self.eval_steps,
            save_strategy=self.save_strategy,
            save_steps=self.save_steps,
            load_best_model_at_end=self.load_best_model_at_end,
            push_to_hub=False,
            eval_accumulation_steps=self.eval_accumulation_steps,
            batch_eval_metrics=False,
            logging_strategy=self.logging_strategy,
            logging_steps=self.logging_steps,
            logging_first_step=self.logging_first_step,
            warmup_ratio=0.1,
            metric_for_best_model="accuracy",
            remove_unused_columns=False,
        )
