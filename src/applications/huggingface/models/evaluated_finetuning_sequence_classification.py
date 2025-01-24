from typing import Dict, List, Mapping, Any, TYPE_CHECKING, Tuple

from pydantic import BaseModel, Field

from applications.huggingface.models.trained_finetuning_sequence_classification import (
    TrainedFineTuningSequenceClassification,
)
from applications.huggingface.tasks.train_task import MeanAccumulator
from ui.field_grid import FieldGrid
from ui.helper import WrappedP6Field, FieldOptions
from ui.sankey_diagram_field import SankeyDiagramField
from ui.tab_field import TabField

if TYPE_CHECKING:
    from core.context.context import Context


class EvaluatedClass(BaseModel):
    label: str

    prediction_map_count: Dict[str, int] = {}
    prediction_map_weight: Dict[str, float] = {}

    expected_count: int = -1
    predicted_count: int = -1
    true_positive_count: int = -1
    true_negative_count: int = -1
    false_positive_count: int = -1
    false_negative_count: int = -1
    recall: float = -1
    precision: float = -1
    f1: float = -1
    accuracy: float = -1

    def process_prediction(self, predicted_label: str, score: float):
        self.prediction_map_count[predicted_label] = (
            self.prediction_map_count.get(predicted_label, 0) + 1
        )
        self.prediction_map_weight[predicted_label] = (
            self.prediction_map_weight.get(predicted_label, 0) + score
        )


class EvaluatedFineTuningSequenceClassification(
    TrainedFineTuningSequenceClassification
):

    META_MODEL = "evaluated_finetuning_sequence_classification"
    HIDDEN_FIELDS = {
        "training_logs",
        "evaluation_logs",
        "labels",
        "chord_matrix_count",
        "chord_matrix_weight",
        "sankey_count_data",
        "evaluated_classes",
    }

    evaluation_tab: TabField = TabField.pydantic(title="Evaluation")
    evaluated_classes: Dict[str, EvaluatedClass] = Field({}, exclude=True)
    labels: List[str] = []
    chord_matrix_count: List[List[int]] = [[]]
    chord_matrix_weight: List[List[float]] = [[]]
    sankey_count_data: Mapping[str, Any] = {}

    metrics_grid: FieldGrid = WrappedP6Field(
        "evaluation_tab", FieldGrid(), title="Metrics"
    )

    mean_recall: float = WrappedP6Field(
        "metrics_grid",
        -1,
        options=FieldOptions.READ_ONLY,
        json_schema_extra={"grid": {"xs": 12, "sm": 3}},
    )
    mean_precision: float = WrappedP6Field(
        "metrics_grid",
        -1,
        options=FieldOptions.READ_ONLY,
        json_schema_extra={"grid": {"xs": 12, "sm": 3}},
    )
    mean_f1: float = WrappedP6Field(
        "metrics_grid",
        -1,
        options=FieldOptions.READ_ONLY,
        json_schema_extra={"grid": {"xs": 12, "sm": 3}},
    )
    mean_accuracy: float = WrappedP6Field(
        "metrics_grid",
        -1,
        options=FieldOptions.READ_ONLY,
        json_schema_extra={"grid": {"xs": 12, "sm": 3}},
    )

    weighted_mean_recall: float = WrappedP6Field(
        "metrics_grid",
        -1,
        options=FieldOptions.READ_ONLY,
        json_schema_extra={"grid": {"xs": 12, "sm": 3}},
    )
    weighted_mean_precision: float = WrappedP6Field(
        "metrics_grid",
        -1,
        options=FieldOptions.READ_ONLY,
        json_schema_extra={"grid": {"xs": 12, "sm": 3}},
    )
    weighted_mean_f1: float = WrappedP6Field(
        "metrics_grid",
        -1,
        options=FieldOptions.READ_ONLY,
        json_schema_extra={"grid": {"xs": 12, "sm": 3}},
    )
    weighted_mean_accuracy: float = WrappedP6Field(
        "metrics_grid",
        -1,
        options=FieldOptions.READ_ONLY,
        json_schema_extra={"grid": {"xs": 12, "sm": 3}},
    )

    sankey_diagram_graph: SankeyDiagramField = WrappedP6Field(
        "metrics_grid",
        SankeyDiagramField(source="sankey_count_data"),
        json_schema_extra={"grid": {"xs": 12, "sm": 12}},
    )

    def before_save_handler(self, context: "Context") -> None:
        super().before_save_handler(context)

        prediction_map: Dict[str, int] = {}

        for label in self.labels:
            self.evaluated_classes.setdefault(label, EvaluatedClass(label=label))
            prediction_map[label] = 0

        for work_label in self.labels:
            true_negative_count = 0
            false_positive_count = 0
            for evaluated_class in self.evaluated_classes.values():
                if evaluated_class.label == work_label:
                    continue

                for (
                    predicted_label,
                    count,
                ) in evaluated_class.prediction_map_count.items():
                    if predicted_label == work_label:
                        false_positive_count += count
                    else:
                        true_negative_count += count

            self.evaluated_classes[work_label].true_negative_count = true_negative_count
            self.evaluated_classes[work_label].false_positive_count = (
                false_positive_count
            )

        for evaluated_class in self.evaluated_classes.values():
            evaluated_class.expected_count = sum(
                evaluated_class.prediction_map_count.values()
            )

            for label, count in evaluated_class.prediction_map_count.items():
                prediction_map[label] += count

        for label, evaluated_class in self.evaluated_classes.items():
            evaluated_class.predicted_count = prediction_map[label]
            evaluated_class.true_positive_count = (
                evaluated_class.prediction_map_count.get(label, 0)
            )
            evaluated_class.false_negative_count = sum(
                (
                    count
                    for prediction_label, count in evaluated_class.prediction_map_count.items()
                    if prediction_label != label
                )
            )

            evaluated_class.recall = (
                evaluated_class.true_positive_count / evaluated_class.expected_count
            )
            evaluated_class.precision = (
                evaluated_class.true_positive_count / evaluated_class.predicted_count
            )

            evaluated_class.f1 = (
                2
                * evaluated_class.precision
                * evaluated_class.recall
                / (evaluated_class.precision + evaluated_class.recall)
            )

            evaluated_class.accuracy = (
                evaluated_class.true_positive_count
                + evaluated_class.true_negative_count
            ) / (
                evaluated_class.true_positive_count
                + evaluated_class.true_negative_count
                + evaluated_class.false_positive_count
                + evaluated_class.false_negative_count
            )

        # first accumulator isn't weighted, second one is
        accumulators: Dict[str, Tuple[MeanAccumulator, MeanAccumulator]] = {}
        metrics = ["recall", "precision", "f1", "accuracy"]
        for metric in metrics:
            accumulators[metric] = (MeanAccumulator(), MeanAccumulator())

        for evaluated_class in self.evaluated_classes.values():
            for metric in metrics:
                metric_value = getattr(evaluated_class, metric)
                weight = float(evaluated_class.expected_count)

                accumulator_simple, accumulator_weighted = accumulators[metric]
                accumulator_simple.add(metric_value)
                accumulator_weighted.add(metric_value, weight)

        for metric in metrics:
            accumulator_simple, accumulator_weighted = accumulators[metric]

            setattr(self, f"mean_{metric}", accumulator_simple.mean())
            setattr(self, f"weighted_mean_{metric}", accumulator_weighted.mean())

        self.chord_matrix_count = [
            [
                self.evaluated_classes[label_x].prediction_map_count.get(label_y, 0)
                for label_y in self.labels
            ]
            for label_x in self.labels
        ]
        self.chord_matrix_weight = [
            [
                self.evaluated_classes[label_x].prediction_map_weight.get(label_y, 0)
                for label_y in self.labels
            ]
            for label_x in self.labels
        ]

        links = []
        for label_x in self.labels:
            for label_y in self.labels:
                value = self.evaluated_classes[label_x].prediction_map_count.get(
                    label_y, 0
                )
                if not value:
                    continue
                links.append(
                    {"source": f"e_{label_x}", "target": f"p_{label_y}", "value": value}
                )

        self.sankey_count_data = {
            "nodes": [{"id": f"e_{label}"} for label in self.labels]
            + [{"id": f"p_{label}"} for label in self.labels],
            "links": links,
        }

    def prepare_evaluation(self, labels: List[str]) -> None:
        self.labels = labels
        self.evaluated_classes.clear()

    def process_prediction(
        self, expected_label: str, predicted_label: str, score: float
    ):
        if expected_label not in self.evaluated_classes:
            self.evaluated_classes[expected_label] = EvaluatedClass(
                label=expected_label
            )

        self.evaluated_classes[expected_label].process_prediction(
            predicted_label, score
        )

    def as_dict(self, **kwargs):

        # self.before_save_handler(None)

        return {
            **super().as_dict(**kwargs),
            "evaluated_classes": {
                key: value.model_dump(mode="json")
                for key, value in self.evaluated_classes.items()
            },
            "labels": self.labels,
            "chord_matrix_count": self.chord_matrix_count,
            "chord_matrix_weight": self.chord_matrix_weight,
            "sankey_count_data": self.sankey_count_data,
            "mean_recall": self.mean_recall,
            "mean_precision": self.mean_precision,
            "mean_f1": self.mean_f1,
            "mean_accuracy": self.mean_accuracy,
            "weighted_mean_recall": self.weighted_mean_recall,
            "weighted_mean_precision": self.weighted_mean_precision,
            "weighted_mean_f1": self.weighted_mean_f1,
            "weighted_mean_accuracy": self.weighted_mean_accuracy,
        }

    @classmethod
    def ui_model_layout(cls) -> str:
        return "tabbed"
