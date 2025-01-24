from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, ClassVar, Mapping, Any

from core.context.global_context import GlobalContext
from core.database.mongodb import MongoDBHandler
from core.models.a_model import AModel
from core.models.types import ModelUsageMode

if TYPE_CHECKING:
    from core.tasks.task_dag import TaskDAG
    from core.context.context import Context


class AChat(AModel):
    META_MODEL = "chat"

    IS_ABSTRACT: ClassVar[bool] = True

    user_id: str
    subject: str

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **super().as_dict(**kwargs),
            "user_id": self.user_id,
            "subject": self.subject or "",
        }

    @property
    def meta_label(self):
        return self.subject

    @abstractmethod
    def as_dag(self) -> "TaskDAG":
        raise NotImplementedError

    @classmethod
    def load_from_mongo(cls, chat_id: str) -> Optional["AChat"]:
        context = GlobalContext.get_instance()
        mongo_db_handler = MongoDBHandler.from_default(context)

        return mongo_db_handler.load_one("chat", {"_id": chat_id})

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        return [
            {
                "source": "user_id",
                "type": "reference",
                "reference": "data/mongodb/user",
            },
            {"source": "subject", "type": "text"},
        ]

    def before_delete_handler(self, context: "Context") -> None:
        super().before_delete_handler(context)
        print("before_delete_handler")
        db_handler = MongoDBHandler.from_default(context)

        messages = list(
            db_handler.load_multiples("chat_messages", {"chat_id": str(self.id)})
        )

        db_handler.delete_model_objects(context, messages, "chat_messages")
