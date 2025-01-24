from typing import TYPE_CHECKING

from datasets import Dataset, ClassLabel
from pydantic import BaseModel, Field
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
from transformers.pipelines.base import KeyDataset

from applications.huggingface.models.evaluated_finetuning_sequence_classification import (
    EvaluatedFineTuningSequenceClassification,
)
from applications.huggingface.models.trained_finetuning_sequence_classification import (
    TrainedFineTuningSequenceClassification,
)
from applications.huggingface.models.training_arguments_model import (
    TrainingArgumentsModel,
)
from applications.huggingface.models.training_finetuning_sequence_classification import (
    TrainingFineTuningSequenceClassification,
)
from applications.huggingface.models.training_label_provider import (
    TrainingLabelProvider,
)
from core.database.mongodb import MongoDBHandler
from core.tasks.task import Task
from core.tasks.types import TaskData

if TYPE_CHECKING:
    from core.context.context import Context


class TitleClassificationEvaluationTask(
    Task["TitleClassificationEvaluationTask.InputModel"]
):

    class UI(BaseModel):
        results: str = Field(title="Results")

    class InputModel(BaseModel):
        class ClassConfig:
            arbitrary_types_allowed = True

        pretrained_model: str
        arguments: TrainingArgumentsModel
        label_provider: TrainingLabelProvider
        model_object: TrainedFineTuningSequenceClassification

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        try:
            data_object = self.input_object(data_in)

            tokenizer = AutoTokenizer.from_pretrained(data_object.pretrained_model)

            evaluated_model = EvaluatedFineTuningSequenceClassification.downcast(
                data_object.model_object
            )

            pretrained_model = AutoModelForSequenceClassification.from_pretrained(
                data_object.arguments.output_dir,
            )

            dataset: Dataset = data_object.model_object.dataset_provider.as_dataset(
                label_provider=data_object.label_provider, split=False
            )

            import torch

            device: int | str = -1  # default value, use CPU
            if torch.cuda.is_available():
                device = 0  # first GPU
            elif torch.backends.mps.is_available():
                device = "mps"  # Metal (mac with ARM chips)

            pipe = pipeline(
                "text-classification",
                model=pretrained_model,
                tokenizer=tokenizer,
                device=device,
            )

            total_len = len(dataset)
            iter_on_predictions = pipe(KeyDataset(dataset, "text"))
            label_feature: ClassLabel = dataset.features["label"]

            evaluated_model.prepare_evaluation(label_feature.names)

            iter_on_label = (
                label_feature.int2str(int_label)
                for int_label in KeyDataset(dataset, "label")
            )

            for idx, (prediction, label) in enumerate(
                zip(iter_on_predictions, iter_on_label)
            ):
                evaluated_model.process_prediction(
                    label, prediction["label"], prediction["score"]
                )
                await self.set_progress(context, float(idx + 1) / float(total_len))

                # break

            from core.context.global_context import GlobalContext

            global_context = context.cast_as(GlobalContext)
            db_handler = MongoDBHandler.from_default(global_context)
            db_handler.save_object(
                global_context,
                evaluated_model,
                TrainingFineTuningSequenceClassification.META_MODEL,
            )

        except Exception as e:
            print(e)

        return {}
