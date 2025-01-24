from applications.huggingface.models.dataset_provider import ADatasetProvider
from applications.huggingface.models.training_arguments_model import (
    TrainingArgumentsModel,
)
from core.models.a_model import AModel
from ui.helper import WrappedP6Field
from ui.tab_field import TabField


class TrainingFineTuningImageClassification(AModel):

    META_MODEL = "training_finetuning_image_classification"

    trained_from: TabField = TabField.pydantic(title="Trained from")
    name: str = WrappedP6Field("trained_from")
    pretrained_model: str = WrappedP6Field(
        "trained_from", "google/vit-base-patch16-224-in21k"
    )

    training_data: TabField = TabField.pydantic(title="Training Data")
    dataset_provider: ADatasetProvider = WrappedP6Field("training_data")

    training_parameters: TabField = TabField.pydantic(title="Training parameters")
    arguments: TrainingArgumentsModel = WrappedP6Field("training_parameters")

    def as_dict(self, **kwargs):
        return {
            **super().as_dict(**kwargs),
            "name": self.name,
            "pretrained_model": self.pretrained_model,
            "dataset_provider": self.dataset_provider.as_dict(),
            "arguments": self.arguments.as_dict(),
        }

    @property
    def meta_label(self) -> str:
        return self.name

    @classmethod
    def ui_model_layout(cls) -> str:
        return "tabbed"
