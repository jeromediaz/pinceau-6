from abc import ABC, abstractmethod, ABCMeta
from typing import Mapping, Any, Optional, TYPE_CHECKING

from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass

if TYPE_CHECKING:
    from core.tasks.task import Task


class ModelMeta(ModelMetaclass, ABCMeta):
    def __new__(mcs, name, bases, dct):
        x = super().__new__(mcs, name, bases, dct)

        return x


class Fieldable(BaseModel, ABC):

    @abstractmethod
    def as_ui_field(self, *, for_task: Optional["Task"] = None) -> Mapping[str, Any]:
        raise NotImplementedError
