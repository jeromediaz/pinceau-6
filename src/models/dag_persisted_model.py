from typing import Any, Mapping, Optional, Dict

from core.models.a_model import AModel
from core.models.types import ModelUsageMode
from models.trigger_model import TriggerModel


class DAGPersistedModel(AModel):
    META_MODEL = "dag_persisted"

    parent_dag_id: str
    dag_id: str
    label: str
    inputs: Mapping[str, Any]
    context: Mapping[str, Any]
    scheduler: Optional[TriggerModel] = None

    def as_dict(self, **kwargs) -> Dict[str, Any]:
        dict_value = {
            **super().as_dict(**kwargs),
            "label": self.label,
            "parent_dag_id": self.parent_dag_id,
            "dag_id": self.dag_id,
            "inputs": self.inputs,
            "context": self.context,
            "scheduler": self.scheduler.as_dict() if self.scheduler else None,
        }
        return dict_value

    @classmethod
    def ui_model_fields(cls, *, display_mode=ModelUsageMode.DEFAULT) -> list:
        return [
            {"source": "label", "type": "text"},
            # TODO: display as field/select and not input in case of edit form
            {"source": "parent_dag_id", "type": "text"},
            {"source": "dag_id", "type": "text"},
            # TODO: display inputs (use model with dynamic model fetching from parent_dag_id)
            {
                "source": "scheduler",
                "type": "model",
                "optional": True,
                "model": "scheduler",
            },
        ]

    def after_save_handler(self, context):
        super().after_save_handler(context)

        from core.context.global_context import GlobalContext

        global_context = context.cast_as(GlobalContext)

        scheduler_manager = global_context.scheduler_manager
        if not scheduler_manager:
            return

        scheduler_manager.schedule_dag(self)

    def after_delete_handler(self, context):
        super().after_save_handler(context)

        from core.context.global_context import GlobalContext

        global_context = context.cast_as(GlobalContext)

        scheduler_manager = global_context.scheduler_manager

        if self.dag_id in global_context.dag_manager:
            del global_context.dag_manager[self.dag_id]

        if not scheduler_manager:
            return

        scheduler_manager.unschedule_dag(self)
