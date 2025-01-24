from typing import List

from applications.huggingface.models.training_finetuning_sequence_classification import (
    TrainingFineTuningSequenceClassification,
)
from ui.ag_charts_field import AGChartsField, AGChartsObject
from ui.helper import WrappedP6Field, FieldOptions
from ui.tab_field import TabField

loss_chart = AGChartsField(source="training_logs")
loss_chart.title["text"] = "Loss evolution"

loss_chart.series.append(
    AGChartsObject(
        type="line",
        xKey="0",
        yKey="1",
        yName="loss",
        marker={"enabled": False},
    )
)
loss_chart.axes.append(AGChartsObject(type="number", position="bottom"))
loss_chart.axes.append(AGChartsObject(type="log", position="left", keys=["1"], base=2))

grad_norm_chart = AGChartsField(source="training_logs")
grad_norm_chart.title["text"] = "Grad Norm evolution"

grad_norm_chart.series.append(
    AGChartsObject(
        type="line",
        xKey="0",
        yKey="2",
        yName="grad_norm",
        marker={"enabled": False},
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


class TrainedFineTuningSequenceClassification(TrainingFineTuningSequenceClassification):

    META_MODEL = "trained_finetuning_sequence_classification"
    HIDDEN_FIELDS = {"training_logs", "evaluation_logs"}

    epoch: float = WrappedP6Field("trained_from", 0.0, options=FieldOptions.READ_ONLY)
    checkpoint_saved: bool = WrappedP6Field(
        "trained_from", False, options=FieldOptions.READ_ONLY
    )
    model_saved: bool = WrappedP6Field(
        "trained_from", False, options=FieldOptions.READ_ONLY
    )

    chart_tab: TabField = TabField.pydantic(title="Training logs")
    loss: AGChartsField = WrappedP6Field("chart_tab", loss_chart)
    grad_norm: AGChartsField = WrappedP6Field("chart_tab", grad_norm_chart)
    eval_loss_chart: AGChartsField = WrappedP6Field("chart_tab", eval_loss_chart)
    eval_accuracy_chart: AGChartsField = WrappedP6Field(
        "chart_tab", eval_accuracy_chart
    )

    training_logs: List[List[float]] = []
    evaluation_logs: List[List[float]] = []

    def as_dict(self, **kwargs):
        return {
            **super().as_dict(**kwargs),
            "epoch": self.epoch,
            "training_logs": self.training_logs,
            "evaluation_logs": self.evaluation_logs,
            "checkpoint_saved": self.checkpoint_saved,
            "model_saved": self.model_saved,
        }

    @classmethod
    def ui_model_layout(cls) -> str:
        return "tabbed"
