import asyncio
from typing import Mapping, Any, TYPE_CHECKING, Optional

from pydantic import BaseModel

from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context


class WaitTask(Task):

    class Parameters(BaseModel):
        wait_duration: int

    def __init__(self, duration: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.args_label = kwargs.get("label")
        if duration is not None:
            self._params["wait_duration"] = duration

    @property
    def label(self) -> str:
        wait_duration = self.params.get("wait_duration")
        return self.args_label if self.args_label else f"Wait {wait_duration}s"

    def clone(self, **kwargs) -> "Task":
        clone_params = {**self.params}
        clone_params.update(kwargs)
        return self.__class__(self._params.get("wait_duration"), **clone_params)

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:

        wait_duration = self.params["wait_duration"]

        await asyncio.sleep(wait_duration)

        return data_input
