from typing import Sequence, Optional

from applications.arxiv.tasks.list_arxiv_search_cat_task import CATEGORIES
from applications.huggingface.models.training_label_provider import (
    TrainingLabelProvider,
)


class CatLabelProvider(TrainingLabelProvider):

    META_MODEL = "training_label_arxiv_cat_provider"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._categories_as_set = set(CATEGORIES)

    @property
    def labels(self) -> Sequence[str]:
        return CATEGORIES

    def matching_label(self, item: str) -> Optional[str]:
        return item if item in CATEGORIES else None
