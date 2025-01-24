from pydantic import BaseModel


class ChatInputModel(BaseModel):
    chat_id: str
    message: str
