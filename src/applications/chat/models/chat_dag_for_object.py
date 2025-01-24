from typing import TYPE_CHECKING, Mapping, Any

from applications.chat.models.a_chat import AChat
from applications.chat.models.chat_dag import ChatDag
from core.context.global_context import GlobalContext
from core.models.types import ModelUsageMode

if TYPE_CHECKING:
    from core.tasks.task_dag import TaskDAG


class ChatDagForObject(ChatDag):
    META_MODEL = "chat_dag_for_object"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.dag_id = kwargs.get("dag_id")

    @classmethod
    def from_default(cls, user_id: str, dag_id: str, subject: str, **kwargs):
        return cls(user_id=user_id, dag_id=dag_id, subject=subject, **kwargs)

    def as_dag(self) -> "TaskDAG":
        # TODO: dynamically create DAG wrapping the original dag

        context = GlobalContext.get_instance()

        base_dag = context.dag_manager[self.dag_id]

        dag_clone = base_dag.clone()

        return dag_clone

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **super().as_dict(**kwargs),
            "input_field": self.input_field,
            "output_field": self.output_field,
            "object_field": self.object_field,
            "object_id": self.object_id,
        }

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        return [
            *AChat.ui_model_fields(),
            {"source": "dag_id", "type": "text"},
            {"source": "input_field", "type": "text"},
            {"source": "output_field", "type": "text"},
            {"source": "object_field", "type": "text"},
            {
                "source": "object_id",
                "type": "text",
            },  # should contain provider and collection
            {
                "source": "dag_parameters",
                "type": "group",
                "multiple": True,
                "opts": ["inline"],
                "fields": [
                    {"source": "key", "type": "text"},
                    {"source": "value", "type": "text"},
                ],
            },
        ]
