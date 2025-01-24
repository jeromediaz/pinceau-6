from typing import Mapping, Any, List, Dict, Optional, TYPE_CHECKING

from pydantic import BaseModel

from ui.fieldable import Fieldable

if TYPE_CHECKING:
    from core.tasks.task import Task


class AGChartsObject(BaseModel):
    # TODO: add validation

    values: Dict[str, Any] = {}

    def __init__(self, **args):
        super().__init__()
        self.values.update(args)

    def __setitem__(self, key, value):
        self.values[key] = value

    def as_map(self):
        return self.values


class AGChartsObjectList(BaseModel):

    values: List[AGChartsObject] = []

    def append(self, value: AGChartsObject):
        self.values.append(value)

    def as_map_list(self):
        return [value.as_map() for value in self.values]


class AGChartsField(Fieldable):

    title: AGChartsObject = AGChartsObject()
    series: AGChartsObjectList = AGChartsObjectList()
    axes: AGChartsObjectList = AGChartsObjectList()

    source: Optional[str] = None

    @property
    def options(self) -> Mapping[str, Any]:

        val = {"title": self.title.as_map(), "series": self.series.as_map_list()}
        axes = self.axes.as_map_list()
        if axes:
            val["axes"] = axes

        return val

    def as_ui_field(self, for_task: Optional["Task"] = None) -> Mapping[str, Any]:
        field = {}

        if self.source:
            field["source"] = self.source

        field.update({"type": "ag_chart", "options": self.options})

        return field
