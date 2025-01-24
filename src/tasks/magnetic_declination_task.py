import datetime
import traceback
from typing import Mapping, Any, TYPE_CHECKING

import aiohttp
from pydantic import BaseModel

from core.tasks.task import Task

now = datetime.datetime.now()
month = now.month

if TYPE_CHECKING:
    from core.context.context import Context


class MagneticDeclinationTask(Task):

    is_passthrough: bool = True

    class InputModel(BaseModel):
        latitude: int
        longitude: int

    class OutputModel(BaseModel):
        data: dict

    async def _process(
        self, context: "Context", data_in: Mapping[str, Any]
    ) -> Mapping[str, Any]:

        input_object = self.input_object(data_in)

        latitude = input_object.latitude
        longitude = input_object.longitude

        params: Mapping[str, str | int] = {
            "lat1": latitude,
            "lon1": longitude,
            "key": "zNEw7",
            "resultFormat": "json",
        }

        try:
            session = aiohttp.ClientSession()
            response = await session.get(
                "https://www.ngdc.noaa.gov/geomag-web/calculators/calculateDeclination",
                params=params,
            )
            content = await response.json(content_type=None)
            await session.close()

            declination = content.get("result")[0].get("declination")

            result = {
                "location": {"type": "Point", "coordinates": [longitude, latitude]},
                "declination": declination,
            }

            return {**data_in, "data": result}

        except Exception as e:
            print(f"{e}")
            traceback.print_exception(e)

        return {}
