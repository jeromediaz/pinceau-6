import json
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, SecretStr


class MongoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.decode("utf-8")
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, BaseModel):
            return obj.model_dump(mode="json", by_alias=True)

        if isinstance(obj, SecretStr):
            return None

        return json.JSONEncoder.default(self, obj)
