from typing import Optional

from datasets import DatasetDict

from core.models.a_model import AModel
from ui.helper import P6Field


class ADatasetProvider(AModel):

    META_MODEL = "dataset_provider"
    IS_ABSTRACT = True

    def as_dataset(self) -> DatasetDict:
        raise NotImplementedError


class HFDatasetProvider(ADatasetProvider):

    META_MODEL = "hf_dataset_provider"

    dataset_path: str
    dataset_split: Optional[str] = None
    test_size: float = P6Field(0.2, gt=0, lt=1)

    def as_dataset(self) -> DatasetDict:
        from datasets import load_dataset

        dataset_split = self.dataset_split
        original_dataset = load_dataset(
            self.dataset_path, split=dataset_split if dataset_split else None
        )

        return original_dataset.train_test_split(test_size=self.test_size)
