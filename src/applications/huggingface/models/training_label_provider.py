from typing import Sequence, Optional

from core.models.a_model import AModel


class TrainingLabelProvider(AModel):

    META_MODEL = "training_label_provider"
    IS_ABSTRACT = True

    @property
    def labels(self) -> Sequence[str]:
        return []

    def matching_label(self, item: str) -> Optional[str]:
        return None

    @property
    def num_labels(self) -> int:
        return len(self.labels)

    @property
    def id2label(self) -> dict[int, str]:
        return {index: label for index, label in enumerate(self.labels)}

    @property
    def label2id(self) -> dict[str, int]:
        return {label: index for index, label in enumerate(self.labels)}
