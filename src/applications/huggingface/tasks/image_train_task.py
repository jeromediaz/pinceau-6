import asyncio
import logging
import os
import weakref
from threading import Thread
from typing import TYPE_CHECKING, Mapping, Any

import psutil
from datasets import DatasetDict
from psutil._common import bytes2human
from pydantic import BaseModel, Field
from transformers import (
    TrainerCallback,
    TrainingArguments,
    TrainerState,
    TrainerControl,
    AutoModelForImageClassification,
)

from applications.huggingface.models.dataset_provider import ADatasetProvider
from applications.huggingface.models.trained_finetuning_image_classification import (
    TrainedFineTuningImageClassification,
)
from applications.huggingface.models.training_arguments_model import (
    TrainingArgumentsModel,
)
from applications.huggingface.models.training_finetuning_image_classification import (
    TrainingFineTuningImageClassification,
)
from core.database.mongodb import MongoDBHandler
from core.tasks.task import Task
from core.tasks.types import TaskData
from tasks.mongo_object_task import MongoObjectTask
from ui.ag_charts_field import AGChartsField, AGChartsObject
from ui.field_grid import FieldGrid
from ui.helper import WrappedP6Field, P6ReferenceField

if TYPE_CHECKING:
    from core.context.context import Context
    from transformers import Trainer


logger = logging.getLogger(__name__)


loss_chart = AGChartsField(source="training_logs")
loss_chart.title["text"] = "Loss"
loss_chart.series.append(
    AGChartsObject(
        type="line", xKey="0", yKey="1", yName="loss", marker={"enabled": False}
    )
)
loss_chart.axes.append(AGChartsObject(type="number", position="bottom"))
loss_chart.axes.append(AGChartsObject(type="number", position="left", keys=["1"]))

grad_norm_chart = AGChartsField(source="training_logs")
grad_norm_chart.title["text"] = "Grad Norm"
grad_norm_chart.series.append(
    AGChartsObject(
        type="line", xKey="0", yKey="2", yName="grad_norm", marker={"enabled": False}
    )
)
grad_norm_chart.axes.append(AGChartsObject(type="number", position="bottom"))
grad_norm_chart.axes.append(AGChartsObject(type="number", position="left", keys=["2"]))


eval_loss_chart = AGChartsField(source="evaluation_logs")
eval_loss_chart.title["text"] = "Loss"
eval_loss_chart.series.append(
    AGChartsObject(
        type="line", xKey="0", yKey="1", yName="eval_loss", marker={"enabled": False}
    )
)
eval_loss_chart.axes.append(AGChartsObject(type="number", position="bottom"))
eval_loss_chart.axes.append(AGChartsObject(type="number", position="left", keys=["1"]))

eval_accuracy_chart = AGChartsField(source="evaluation_logs")
eval_accuracy_chart.title["text"] = "Accuracy"
eval_accuracy_chart.series.append(
    AGChartsObject(
        type="line",
        xKey="0",
        yKey="2",
        yName="eval_accuracy",
        marker={"enabled": False},
    )
)
eval_accuracy_chart.axes.append(AGChartsObject(type="number", position="bottom"))
eval_accuracy_chart.axes.append(
    AGChartsObject(type="number", position="left", keys=["2"])
)


class ProgressionCallBack(TrainerCallback):

    def __init__(
        self,
        context: "Context",
        task: Task,
        total_epoch: float,
        model: TrainedFineTuningImageClassification,
        trainer: "Trainer",
        loop: "asyncio.AbstractEventLoop",
    ):
        self._context = weakref.ref(context)
        self._task = weakref.ref(task)
        self._total_epoch = total_epoch
        self._model = weakref.ref(model)
        self._trainer = weakref.ref(trainer)
        self._loop = loop
        super().__init__()

    async def __emit_data(self, state: TrainerState):
        process = psutil.Process(os.getpid())
        mem_info = process.memory_full_info()

        context = self._context()
        task = self._task()

        if not context or not task:
            return

        await context.event(
            task,
            "data",
            {
                "global_step": f"{state.global_step:_}",
                "max_step": f"{state.max_steps:_}",
                "epoch": f"{state.epoch}",
                "num_train_epochs": f"{state.num_train_epochs}",
                "memory": f"RSS {bytes2human(mem_info.rss)}  USS {bytes2human(mem_info.uss)}",
            },
        )

    def on_train_begin(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        **kwargs,
    ):

        def target():
            asyncio.run(self.__emit_data(state))

        t = Thread(target=target)
        t.start()

    def on_train_end(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        **kwargs,
    ):
        def target():
            asyncio.run(self.__emit_data(state))

        t = Thread(target=target)
        t.start()

    def on_log(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        **kwargs,
    ):
        async def sub_target() -> None:
            logs: Mapping[str, Any] = kwargs.get("logs", {}) if kwargs else {}

            context = self._context()
            task = self._task()
            model = self._model()

            if not context or not task or not model:
                return

            if state.epoch > 0 and "loss" in logs and "grad_norm" in logs:
                await context.event(
                    task,
                    "stream",
                    {
                        "training_logs": (
                            [[state.epoch, logs["loss"], logs["grad_norm"]]],
                            False,
                        ),
                    },
                )

                model.training_logs.append(
                    [state.epoch, logs["loss"], logs["grad_norm"]]
                )

            if state.epoch > 0 and "eval_accuracy" in logs and "eval_loss" in logs:
                await context.event(
                    task,
                    "stream",
                    {
                        "evaluation_logs": (
                            [
                                [
                                    state.epoch,
                                    logs["eval_loss"],
                                    logs["eval_accuracy"],
                                ]
                            ],
                            False,
                        ),
                    },
                )

                model.evaluation_logs.append(
                    [state.epoch, logs["eval_loss"], logs["eval_accuracy"]]
                )

        def target():
            asyncio.run(sub_target())

            asyncio.run(self.__emit_data(state))

        t = Thread(target=target)
        t.start()

    def on_save(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        **kwargs,
    ):
        context = self._context()
        task = self._task()
        model = self._model()
        trainer = self._trainer()

        if not context or not task or not model or not trainer:
            return

        model.checkpoint_saved = True
        model.epoch = state.epoch

        db_handler = MongoDBHandler.from_default(context)

        db_handler.save_object(
            context, model, TrainingFineTuningImageClassification.META_MODEL
        )


class MeanAccumulator:
    def __init__(self) -> None:
        self._accumulator: float = 0.0
        self._total_weight: float = 0

    def add(self, value: float, weight: float = 1.0):
        self._accumulator += value * weight
        self._total_weight += weight

    def mean(self) -> float:
        return self._accumulator / self._total_weight

    def is_empty(self) -> bool:
        return self._total_weight == 0.0

    def reset(self):
        self._accumulations = 0
        self._accumulator = 0.0


def split_data_handler(
    task, context, model_object: TrainingFineTuningImageClassification, **kwargs
):
    return {
        **kwargs,
        "model_object": model_object,
        "dataset_provider": model_object.dataset_provider,
        "pretrained_model": model_object.pretrained_model,
        "arguments": model_object.arguments,
    }


class SplitData(MongoObjectTask):

    class OutputModel(BaseModel):
        class Config:
            arbitrary_types_allowed = True

        pretrained_model: str
        dataset_provider: DatasetDict
        arguments: TrainingArgumentsModel
        model_object: TrainingFineTuningImageClassification

    def __init__(self, *args, **kwargs):
        requires_trained_model = kwargs.get("requires_trained_model", False)
        kwargs.pop("input_name", None)
        kwargs.pop("output_name", None)
        kwargs.pop("model", None)
        kwargs.pop("handler", None)
        super().__init__(
            source=TrainingFineTuningImageClassification.META_MODEL,
            model=(
                TrainingFineTuningImageClassification.META_MODEL
                if not requires_trained_model
                else TrainedFineTuningImageClassification.META_MODEL
            ),
            handler=split_data_handler,
            input_name="object_id",
            output_name="model_object",
            **kwargs,
        )

    def clone(self, **kwargs) -> "Task":
        return self.__class__(**self.params, **kwargs)


class ImageTrainPrepareDataset(Task["ImageTrainPrepareDataset.InputModel"]):

    class InputModel(BaseModel):
        dataset_provider: ADatasetProvider

    class OutputModel(BaseModel):
        dataset_provider: ADatasetProvider

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        data_object = self.input_object(data_in)

        dataset_provider = data_object.dataset_provider.as_dataset()

        return {**data_in, "dataset_provider": dataset_provider}


class ImageTrainTask(Task["ImageTrainTask.InputModel"]):

    class UI(BaseModel):
        step_grid: FieldGrid = Field(FieldGrid(), title="Step")
        global_step: str = WrappedP6Field("step_grid", title="Global Step")
        max_step: str = WrappedP6Field("step_grid", title="Max Steps")

        epoch_grid: FieldGrid = Field(FieldGrid(), title="Epoch")
        epoch: str = WrappedP6Field("epoch_grid", title="Epoch")
        num_train_epochs: str = WrappedP6Field("epoch_grid", title="Train Epochs")

        memory: str = Field(title="Memory")
        training_chart: AGChartsField = Field(loss_chart, title="Training")
        training_chart_1: AGChartsField = Field(grad_norm_chart, title="Training")
        training_chart_2: AGChartsField = Field(eval_loss_chart, title="Evaluation")
        training_chart_3: AGChartsField = Field(eval_accuracy_chart, title="Evaluation")

    class InputModel(BaseModel):
        class Config:
            arbitrary_types_allowed = True

        model_object: str = P6ReferenceField(
            reference=f"data/mongodb/{TrainingFineTuningImageClassification.META_MODEL}"
        )

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        data_input_object = self.input_object(data_in)

        db_handler = MongoDBHandler.from_default(context)

        data_object = db_handler.get_instance(
            TrainingFineTuningImageClassification,
            TrainingFineTuningImageClassification.META_MODEL,
            data_input_object.model_object,
        )

        from transformers import (
            AutoImageProcessor,
            Trainer,
            DefaultDataCollator,
        )

        dataset = data_object.dataset_provider.as_dataset()

        labels = dataset["train"].features["label"].names
        label2id, id2label = {}, {}
        for i, label in enumerate(labels):
            label2id[label] = str(i)
            id2label[str(i)] = label

        image_processor = AutoImageProcessor.from_pretrained(
            data_object.pretrained_model, use_fast=True
        )

        from torchvision.transforms import (
            RandomResizedCrop,
            Compose,
            Normalize,
            ToTensor,
        )

        normalize = Normalize(
            mean=image_processor.image_mean, std=image_processor.image_std
        )
        size = (
            image_processor.size["shortest_edge"]
            if "shortest_edge" in image_processor.size
            else (image_processor.size["height"], image_processor.size["width"])
        )
        _transforms = Compose([RandomResizedCrop(size), ToTensor(), normalize])

        def transforms(examples):
            examples["pixel_values"] = [
                _transforms(img.convert("RGB")) for img in examples["image"]
            ]
            del examples["image"]
            return examples

        dataset = dataset.with_transform(transforms)
        data_collator = DefaultDataCollator()

        import evaluate

        accuracy = evaluate.load("accuracy")

        import numpy as np

        def compute_metrics(eval_pred):
            predictions, labels = eval_pred
            predictions = np.argmax(predictions, axis=1)
            return accuracy.compute(predictions=predictions, references=labels)

        model = AutoModelForImageClassification.from_pretrained(
            data_object.pretrained_model,
            num_labels=len(id2label),
            id2label=id2label,
            label2id=label2id,
        )

        model.to("mps")

        training_args = data_object.arguments.as_training_arguments()

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset["train"],
            eval_dataset=dataset["test"],
            processing_class=image_processor,
            data_collator=data_collator,
            compute_metrics=compute_metrics,
            # preprocess_logits_for_metrics=preprocess_logits_for_metrics,
        )

        if isinstance(data_object.model_object, TrainedFineTuningImageClassification):
            await context.event(
                self,
                "stream",
                {
                    "training_logs": (
                        data_object.model_object.training_logs,
                        True,
                    ),
                },
            )

            await context.event(
                self,
                "stream",
                {
                    "evaluation_logs": (
                        data_object.evaluation_logs,
                        False,
                    ),
                },
            )

        trained_model = TrainedFineTuningImageClassification.downcast(data_object)

        import nest_asyncio

        nest_asyncio.apply()
        loop = asyncio.get_event_loop()

        callback = ProgressionCallBack(
            context,
            self,
            data_object.arguments.nƒum_train_epochs,
            trained_model,
            trainer,
            loop,
        )
        try:
            trainer.add_callback(callback)
            trainer.train()
            # trainer.train(resume_from_checkpoint=trained_model.checkpoint_saved)
            trainer.save_model()

            trainer.remove_callback(callback)

            trained_model.model_saved = True

            db_handler = MongoDBHandler.from_default(context)

            db_handler.save_object(
                context,
                trained_model,
                TrainingFineTuningImageClassification.META_MODEL,
            )
        except Exception as e:
            print(e)

        return {}
