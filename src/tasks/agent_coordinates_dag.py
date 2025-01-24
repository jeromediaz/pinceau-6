from typing import TYPE_CHECKING

from pydantic import BaseModel

from core.context.composite_context import CompositeContext
from core.tasks.task import Task
from core.tasks.types import TaskData

if TYPE_CHECKING:
    from core.context.context import Context


class AgentCoordinatesDag(Task["AgentCoordinatesDag.InputModel"]):

    class InputModel(BaseModel):
        lat: int
        lng: int
        dag: str = "mag"

    async def _process(self, context: "Context", data_input: TaskData) -> TaskData:
        if not isinstance(context, CompositeContext):
            raise ValueError(
                f"{self.__class__.__name__} context should be a CompositeContext"
            )

        print(f"Process agent AgentCoordinatesDag {self.id}")

        input_model_object = self.input_object(data_input)

        try:
            coordinates = {
                "latitude": input_model_object.lat,
                "longitude": input_model_object.lng,
                "mongodb_database": "test",
                "collection": "test_range_mag",
            }
            await context.run_dag(
                context.dag_manager[input_model_object.dag], coordinates
            )
        except Exception as e:
            print(e)

        return {}
