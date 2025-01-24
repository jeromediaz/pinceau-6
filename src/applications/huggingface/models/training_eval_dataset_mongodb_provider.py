from typing import TYPE_CHECKING, Mapping, Any, ClassVar

from datasets import Dataset
from pydantic import Field

from applications.huggingface.models.training_eval_dataset_provider import (
    TrainingEvalDatasetProvider,
)
from misc.mongodb_helper import mongodb_collection

if TYPE_CHECKING:
    from datasets import DatasetDict
    from applications.huggingface.models.training_label_provider import (
        TrainingLabelProvider,
    )


class TrainingEvalDatasetMongodbProvider(TrainingEvalDatasetProvider):

    META_MODEL: ClassVar[str] = "training_eval_dataset_mongodb_cat_provider"

    dbms_link: str = "mongodb_mm1"
    database: str = "saaswedo"
    collection: str = "arxiv"
    label_field: str = "category"
    text_field: str = "title"
    test_size: float = Field(0.2, gt=0, lt=1)

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **super().as_dict(**kwargs),
            "dbms_link": self.dbms_link,
            "database": self.database,
            "collection": self.collection,
            "label_field": self.label_field,
            "text_field": self.text_field,
            "test_size": self.test_size,
        }

    def as_dataset(self, **kwargs) -> "DatasetDict|Dataset":
        from datasets import Dataset

        label_provider: "TrainingLabelProvider" = kwargs["label_provider"]
        split = kwargs.get("split", True)

        from core.context.global_context import GlobalContext

        context = GlobalContext().get_instance()

        def gen():
            # the mongodb fields to use as label and text to classify
            label_field = self.label_field
            text_field = self.text_field

            # get the mongodb collection to use for this dataset
            db_collection = mongodb_collection(
                context, self.dbms_link, self.database, self.collection
            )

            # iterate on all rows for the dataset
            cursor = db_collection.find({})
            for row in cursor:
                label = label_provider.matching_label(row[label_field])

                if label is None:
                    continue

                text = row[text_field]

                yield {"label": label, "text": text}

        mongo_dataset = Dataset.from_generator(gen)

        # indicates that the "label" column is used as a class
        mongo_dataset = mongo_dataset.class_encode_column("label")

        if split:
            # split the dataset into two parts, "train" and "test"
            return mongo_dataset.train_test_split(
                test_size=self.test_size,  # 0.2
                # to respect the ratio of samples for a given class
                stratify_by_column="label",
            )
        else:
            return mongo_dataset
