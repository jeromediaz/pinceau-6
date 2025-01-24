from typing import TYPE_CHECKING

from core.models.a_model import AModel

if TYPE_CHECKING:
    from datasets import DatasetDict


class TrainingEvalDatasetProvider(AModel):

    META_MODEL = "training_eval_dataset_provider"
    IS_ABSTRACT = True

    def as_dataset(self, **kwargs) -> "DatasetDict":
        raise NotImplementedError()
