import logging
from abc import ABC

import arxiv
from pydantic import BaseModel

from core.tasks.task import Task

logging.basicConfig(level=logging.DEBUG)


class IndexArxivResult(Task["IndexArxivResult.InputModel"], ABC):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class InputModel(BaseModel):
        class Config:
            arbitrary_types_allowed = True

        subject: str
        result: arxiv.Result
