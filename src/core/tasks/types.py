from enum import Enum
from typing import Union, Dict, List, Any, Mapping, AsyncIterator

JSONValue = Union[
    str, int, float, bool, None, Dict[str, "JSONValue"], List["JSONValue"]
]
JSONType = Union[Dict[str, JSONValue], List[JSONValue]]
JSONParam = Dict[str, JSONValue]

TaskData = Mapping[str, Any]
TaskDataAsyncIterator = AsyncIterator[TaskData]


class Status(Enum):
    IDLE = 0
    WAITING = 1
    SCHEDULED = 2
    RUNNING = 3
    FINISHED = 4
    ERROR = -1


class TaskEdgeKind(Enum):
    DEFAULT = 0
    DIRECT = 1
    CONDITIONAL = 2
    LOOP = 3
    LOOP_START = 4
    LOOP_END = 5


class ProcessMode(Enum):
    UNKNOWN = 0
    NORMAL = 1
    GENERATOR = 2
