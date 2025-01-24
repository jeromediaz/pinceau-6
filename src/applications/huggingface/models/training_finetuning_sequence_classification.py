from applications.huggingface.models.training_arguments_model import (
    TrainingArgumentsModel,
)
from applications.huggingface.models.training_eval_dataset_provider import (
    TrainingEvalDatasetProvider,
)
from applications.huggingface.models.training_label_provider import (
    TrainingLabelProvider,
)
from core.models.a_model import AModel
from ui.helper import WrappedP6Field
from ui.tab_field import TabField


class TrainingFineTuningSequenceClassification(AModel):

    META_MODEL = "training_finetuning_sequence_classification"

    trained_from: TabField = TabField.pydantic(title="Trained from")
    name: str = WrappedP6Field("trained_from")
    pretrained_model: str = WrappedP6Field(
        "trained_from", "distilbert/distilbert-base-uncased"
    )

    training_data: TabField = TabField.pydantic(title="Training Data")
    label_provider: TrainingLabelProvider = WrappedP6Field("training_data")
    dataset_provider: TrainingEvalDatasetProvider = WrappedP6Field("training_data")

    training_parameters: TabField = TabField.pydantic(title="Training parameters")
    arguments: TrainingArgumentsModel = WrappedP6Field("training_parameters")

    def as_dict(self, **kwargs):
        return {
            **super().as_dict(**kwargs),
            "name": self.name,
            "pretrained_model": self.pretrained_model,
            "label_provider": self.label_provider.as_dict(),
            "dataset_provider": self.dataset_provider.as_dict(),
            "arguments": self.arguments.as_dict(),
        }

    @property
    def meta_label(self) -> str:
        return self.name

    @classmethod
    def ui_model_layout(cls) -> str:
        return "tabbed"
