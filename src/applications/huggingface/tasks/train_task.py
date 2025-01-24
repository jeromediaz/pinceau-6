import asyncio
import logging
import os
import weakref
from typing import TYPE_CHECKING, Mapping, Any, Set

import psutil
import torch
from datasets import DatasetDict
from psutil._common import bytes2human
from pydantic import BaseModel, Field
from transformers import (
    TrainerCallback,
    TrainingArguments,
    TrainerState,
    TrainerControl,
)

from applications.huggingface.models.trained_finetuning_sequence_classification import (
    TrainedFineTuningSequenceClassification,
)
from applications.huggingface.models.training_arguments_model import (
    TrainingArgumentsModel,
)
from applications.huggingface.models.training_eval_dataset_provider import (
    TrainingEvalDatasetProvider,
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
from tasks.mongo_object_task import MongoObjectTask
from ui.ag_charts_field import AGChartsField, AGChartsObject
from ui.field_grid import FieldGrid
from ui.helper import WrappedP6Field

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
        model: TrainedFineTuningSequenceClassification,
        trainer: "Trainer",
        loop: "asyncio.AbstractEventLoop",
    ):
        self._context = weakref.ref(context)
        self._task = weakref.ref(task)
        self._total_epoch = total_epoch
        self._model = weakref.ref(model)
        self._trainer = weakref.ref(trainer)
        self._futures: Set["asyncio.Future"] = set()
        self._loop = loop
        super().__init__()

    def _keep_future_until_done(self, future: "asyncio.Future"):
        self._futures.add(future)
        future.add_done_callback(lambda fut: self._futures.remove(fut))

    def __emit_data(self, state: TrainerState):
        process = psutil.Process(os.getpid())
        mem_info = process.memory_full_info()

        context = self._context()
        task = self._task()

        if not context or not task:
            return

        self._keep_future_until_done(
            asyncio.ensure_future(
                context.event(
                    task,
                    "data",
                    {
                        "global_step": f"{state.global_step:_}",
                        "max_step": f"{state.max_steps:_}",
                        "epoch": f"{state.epoch}",
                        "num_train_epochs": f"{state.num_train_epochs}",
                        "memory": f"RSS {bytes2human(mem_info.rss)}  USS {bytes2human(mem_info.uss)}",
                    },
                ),
                loop=self._loop,
            )
        )

    def on_train_begin(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        **kwargs,
    ):
        self.__emit_data(state)

    def on_train_end(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        **kwargs,
    ):
        self.__emit_data(state)

    def on_log(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        **kwargs,
    ):
        logs: Mapping[str, Any] = kwargs.get("logs", {}) if kwargs else {}

        context = self._context()
        task = self._task()
        model = self._model()

        if not context or not task or not model:
            return

        if state.epoch > 0 and "loss" in logs and "grad_norm" in logs:
            self._keep_future_until_done(
                asyncio.ensure_future(
                    context.event(
                        task,
                        "stream",
                        {
                            "training_logs": (
                                [[state.epoch, logs["loss"], logs["grad_norm"]]],
                                False,
                            ),
                        },
                    ),
                    loop=self._loop,
                )
            )

            model.training_logs.append([state.epoch, logs["loss"], logs["grad_norm"]])

        if state.epoch > 0 and "eval_accuracy" in logs and "eval_loss" in logs:
            self._keep_future_until_done(
                asyncio.ensure_future(
                    context.event(
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
                    ),
                    loop=self._loop,
                )
            )

            model.evaluation_logs.append(
                [state.epoch, logs["eval_loss"], logs["eval_accuracy"]]
            )

        self.__emit_data(state)

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

        from core.context.global_context import GlobalContext

        db_handler = MongoDBHandler.from_default(context)
        global_context = context.cast_as(GlobalContext)

        db_handler.save_object(
            global_context, model, TrainingFineTuningSequenceClassification.META_MODEL
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
    task, context, model_object: TrainingFineTuningSequenceClassification, **kwargs
):
    label_provider = model_object.label_provider

    return {
        **kwargs,
        "model_object": model_object,
        "label_provider": label_provider,
        "dataset_provider": model_object.dataset_provider,
        "pretrained_model": model_object.pretrained_model,
        "arguments": model_object.arguments,
    }


class SplitData(MongoObjectTask):

    def __init__(self, *args, **kwargs):
        requires_trained_model = kwargs.get("requires_trained_model", False)
        kwargs.pop("input_name", None)
        kwargs.pop("output_name", None)
        kwargs.pop("model", None)
        kwargs.pop("handler", None)
        super().__init__(
            source=TrainingFineTuningSequenceClassification.META_MODEL,
            model=(
                TrainingFineTuningSequenceClassification.META_MODEL
                if not requires_trained_model
                else TrainedFineTuningSequenceClassification.META_MODEL
            ),
            handler=split_data_handler,
            input_name="object_id",
            output_name="model_object",
            **kwargs,
        )

    def clone(self, **kwargs) -> "Task":
        return self.__class__(**self.params, **kwargs)


class ArxivTrainPrepareTask(Task["ArxivTrainPrepareTask.InputModel"]):

    class InputModel(BaseModel):
        label_provider: TrainingLabelProvider
        dataset_provider: TrainingEvalDatasetProvider

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        data_object = self.input_object(data_in)

        label_provider = data_object.label_provider
        dataset = data_object.dataset_provider.as_dataset(label_provider=label_provider)

        return {**data_in, "dataset": dataset}


class ArxivTrainTask(Task["ArxivTrainTask.InputModel"]):

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

        pretrained_model: str
        label_provider: TrainingLabelProvider
        dataset: DatasetDict
        arguments: TrainingArgumentsModel
        model_object: TrainingFineTuningSequenceClassification

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:
        data_object = self.input_object(data_in)

        from transformers import (
            AutoTokenizer,
            DataCollatorWithPadding,
            AutoModelForSequenceClassification,
            Trainer,
        )

        import evaluate

        tokenizer = AutoTokenizer.from_pretrained(data_object.pretrained_model)

        def preprocess_function(sample):
            return tokenizer(sample["text"], truncation=True)

        tokenized_dataset = data_object.dataset.map(preprocess_function, batched=True)

        data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

        accuracy = evaluate.load("accuracy")

        mean_accuracy = MeanAccumulator()

        def compute_metrics(eval_pred, compute_result: bool = True):
            predictions, labels = eval_pred

            computed_accuracy = accuracy.compute(
                predictions=predictions,
                references=labels,
            )

            if compute_result and mean_accuracy.is_empty():
                return computed_accuracy

            mean_accuracy.add(computed_accuracy["accuracy"])

            if compute_result:
                result_value = {"accuracy": mean_accuracy.mean()}
                mean_accuracy.reset()

                return result_value

        def preprocess_logits_for_metrics(logits, labels):
            if isinstance(logits, tuple):
                # Depending on the model and config, logits may contain extra tensors,
                # like past_key_values, but logits always come first
                logits = logits[0]
                # argmax to get the token ids
            return torch.argmax(logits, dim=-1)

        label_feature = tokenized_dataset["train"].features["label"]
        id2label = {}
        label2id = {}
        for idx, name in enumerate(label_feature.names):
            id2label[idx] = name
            label2id[name] = idx

        model = AutoModelForSequenceClassification.from_pretrained(
            data_object.pretrained_model,
            num_labels=len(id2label),
            id2label=id2label,
            label2id=label2id,
        )

        training_args = data_object.arguments.as_training_arguments()

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset["train"],
            eval_dataset=tokenized_dataset["test"],
            tokenizer=tokenizer,
            data_collator=data_collator,
            compute_metrics=compute_metrics,
            preprocess_logits_for_metrics=preprocess_logits_for_metrics,
        )

        if isinstance(
            data_object.model_object, TrainedFineTuningSequenceClassification
        ):
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
                        data_object.model_object.evaluation_logs,
                        False,
                    ),
                },
            )

        trained_model = TrainedFineTuningSequenceClassification.downcast(
            data_object.model_object
        )

        callback = ProgressionCallBack(
            context,
            self,
            data_object.arguments.nƒum_train_epochs,
            trained_model,
            trainer,
            asyncio.get_running_loop(),
        )
        try:
            trainer.add_callback(callback)

            trainer.train(resume_from_checkpoint=trained_model.checkpoint_saved)
            trainer.save_model()

            trainer.remove_callback(callback)

            trained_model.model_saved = True

            from core.context.global_context import GlobalContext

            global_context = context.cast_as(GlobalContext)
            db_handler = MongoDBHandler.from_default(global_context)

            db_handler.save_object(
                global_context,
                trained_model,
                TrainingFineTuningSequenceClassification.META_MODEL,
            )
        except Exception as e:
            print(e)

        return {}
