from typing import TYPE_CHECKING, Any, Mapping, Optional

from pydantic import BaseModel

from core.tasks.task import Task
from core.tasks.types import Status

if TYPE_CHECKING:
    from core.context.context import Context


class AgentEcho(Task["AgentEcho.InputModel"]):

    class InputModel(BaseModel):
        expected_iterations: int

    def __init__(self, **kwargs):
        kwargs.setdefault("is_passthrough", True)
        super().__init__(**kwargs)
        self._iteration = 0

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:

        input_value = self.input_object(data_input)

        self._iteration += 1

        await self.set_progress(
            context,
            float(self._iteration) / input_value.expected_iterations,
        )

        return data_input

    async def set_status(
        self,
        context: "Context",
        value: "Status",
        /,
        *,
        error: Optional[Exception] = None,
        send_value: bool = True,
        **kwargs,
    ):
        if value == Status.IDLE:
            self._iteration = 0

        await super().set_status(
            context, value, send_value=send_value, error=error, **kwargs
        )
