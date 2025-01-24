from typing import Mapping, Any, Set

from apscheduler.triggers.base import BaseTrigger

from core.models.a_model import AModel
from core.models.types import ModelUsageMode

_JITTER_FIELD = {
    "source": "jitter",
    "type": "int",
    "defaultValue": 0,
    "optional": True,
    "number": {"min": 0},
}


class TriggerModel(AModel):
    META_MODEL = "scheduler"

    IS_ABSTRACT = True

    ALLOWED_PARAMS: Set[str] = set()

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        return []

    def as_trigger(self) -> BaseTrigger:
        raise NotImplementedError

    def _get_parameters(self) -> Mapping[str, Any]:
        model_extra = self.model_extra
        if not model_extra:
            return {}

        return {k: v for k, v in model_extra.items() if k in self.ALLOWED_PARAMS}


class DateTriggerModel(TriggerModel):
    META_MODEL = "date_trigger"

    ALLOWED_PARAMS: Set[str] = {"run_date", "timezone"}

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:

        return [
            {"source": "run_date", "type": "datetime", "optional": True},
            {"source": "timezone", "type": "text", "optional": True},
        ]

    def as_trigger(self) -> BaseTrigger:
        from apscheduler.triggers.date import DateTrigger

        params = self._get_parameters()
        return DateTrigger(**params)


class IntervalTriggerModel(TriggerModel):
    META_MODEL = "interval_trigger"

    ALLOWED_PARAMS: Set[str] = {
        "weeks",
        "days",
        "hours",
        "minutes",
        "seconds",
        "start_date",
        "end_date",
        "timezone",
        "jitter",
    }

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:

        return [
            {"source": "weeks", "type": "int", "defaultValue": 0},
            {"source": "days", "type": "int", "defaultValue": 0},
            {"source": "hours", "type": "int", "defaultValue": 0, "range": {"min": 0}},
            {
                "source": "minutes",
                "type": "int",
                "defaultValue": 0,
                "range": {"min": 0},
            },
            {
                "source": "seconds",
                "type": "int",
                "defaultValue": 0,
                "range": {"min": 0},
            },
            {"source": "start_date", "type": "datetime", "optional": True},
            {"source": "end_date", "type": "datetime", "optional": True},
            {"source": "timezone", "type": "text", "optional": True},
            _JITTER_FIELD,
        ]

    def as_trigger(self) -> BaseTrigger:
        from apscheduler.triggers.interval import IntervalTrigger

        params = self._get_parameters()
        return IntervalTrigger(**params)


class CronTriggerModel(TriggerModel):
    META_MODEL = "cron_trigger"

    ALLOWED_PARAMS: Set[str] = {
        "year",
        "month",
        "day",
        "week",
        "day_of_week",
        "hour",
        "minute",
        "second",
        "start_date",
        "end_date",
        "timezone",
        "jitter",
    }

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:

        return [
            {
                "source": "year",
                "type": "int",
                "defaultValue": 0,
                "optional": True,
                "number": {"min": 2000},
            },
            {
                "source": "month",
                "type": "int",
                "defaultValue": 0,
                "optional": True,
                "number": {"min": 1, "max": 12},
            },
            {
                "source": "day",
                "type": "int",
                "defaultValue": 0,
                "optional": True,
                "number": {"min": 1, "max": 31},
            },
            {
                "source": "week",
                "type": "int",
                "defaultValue": 0,
                "optional": True,
                "number": {"min": 1, "max": 53},
            },
            {
                "source": "day_of_week",
                "type": "select",
                "optional": True,
                "choices": [
                    {"id": "mon", "name": "Monday"},
                    {"id": "tue", "name": "Tuesday"},
                    {"id": "wed", "name": "Wednesday"},
                    {"id": "thu", "name": "Thursday"},
                    {"id": "fri", "name": "Friday"},
                    {"id": "sat", "name": "Saturday"},
                    {"id": "sun", "name": "Sunday"},
                ],
            },
            {
                "source": "hour",
                "type": "int",
                "defaultValue": 0,
                "optional": True,
                "number": {"min": 0, "max": 23},
            },
            {
                "source": "minute",
                "type": "int",
                "defaultValue": 0,
                "optional": True,
                "number": {"min": 0, "max": 59},
            },
            {
                "source": "second",
                "type": "int",
                "defaultValue": 0,
                "optional": True,
                "number": {"min": 0, "max": 59},
            },
            {"source": "start_date", "type": "datetime", "optional": True},
            {"source": "end_date", "type": "datetime", "optional": True},
            {"source": "timezone", "type": "text", "optional": True},
            _JITTER_FIELD,
        ]

    def as_trigger(self) -> BaseTrigger:
        from apscheduler.triggers.cron import CronTrigger

        params = self._get_parameters()
        return CronTrigger(**params)


class CombiningTriggerModel(TriggerModel):
    META_MODEL = "combining_trigger"

    ALLOWED_PARAMS: Set[str] = {
        "triggers",
        "jitter",
    }

    IS_ABSTRACT = True

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        return [
            {
                "source": "triggers",
                "type": "model",
                "model": "scheduler",
                "multiple": True,
            },
            _JITTER_FIELD,
        ]


class OrTriggerModel(CombiningTriggerModel):
    META_MODEL = "or_trigger"

    def as_trigger(self) -> BaseTrigger:
        from apscheduler.triggers.combining import OrTrigger

        params = self._get_parameters()
        return OrTrigger(**params)


class AndTriggerModel(CombiningTriggerModel):
    META_MODEL = "and_trigger"

    def as_trigger(self) -> BaseTrigger:
        from apscheduler.triggers.combining import AndTrigger

        params = self._get_parameters()
        return AndTrigger(**params)
