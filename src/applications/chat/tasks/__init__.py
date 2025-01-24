from pydantic import BaseModel

from core.tasks.task import Task


class BaseChatTask(Task["BaseChatTask.InputModel"]):  # TODO: add ABC

    TAGS = ["chat"]

    class InputModel(BaseModel):
        chat_id: str
        message: str
