from typing import TYPE_CHECKING, Mapping, Any

from applications.chat.models.chat_dag import ChatDag
from applications.chat.tasks.chat_input_mapping import ChatInputMapping
from applications.chat.tasks.chat_output_mapping import ChatOutputMapping
from core.context.global_context import GlobalContext

if TYPE_CHECKING:
    from core.tasks.task_dag import TaskDAG


class ChatFromWrappedDag(ChatDag):
    META_MODEL = "chat_from_wrapped_dag"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.dag_id = kwargs.get("dag_id")
        self.input_field = kwargs.get("input_field")
        self.input_type = kwargs.get("input_type")
        self.output_field = kwargs.get("output_field")
        self.output_type = kwargs.get("output_type")
        self.job_payload = kwargs.get("job_payload", {})

    @property
    def meta_label(self):
        return f"{self.dag_id} - {self.subject}"

    @classmethod
    def from_default(cls, user_id: str, dag_id: str, subject: str, **kwargs):
        return cls(user_id=user_id, dag_id=dag_id, subject=subject, **kwargs)

    def as_dag(self) -> "TaskDAG":
        expected_wrapped_dag_id = f"{self.dag_id}:chat_{self.id}"

        context = GlobalContext.get_instance()

        if expected_wrapped_dag_id in context.dag_manager:
            return context.dag_manager[expected_wrapped_dag_id]

        base_dag = context.dag_manager[self.dag_id]

        with base_dag.clone(new_id=expected_wrapped_dag_id) as dag_clone:
            if self.input_field != "message" or self.input_type == "str":
                root_tasks = dag_clone.get_root_tasks().copy()

                prior_task = ChatInputMapping(
                    dag=dag_clone,
                    id="root-task",
                    input_field=self.input_field,
                    input_type=self.input_type,
                )

                for root_task in root_tasks:
                    prior_task >> root_task
                    # prior task is now the root_task

            leaf_tasks = dag_clone.get_leaf_tasks()
            for idx, leaf_task in enumerate(leaf_tasks):
                after_task = ChatOutputMapping(
                    dag=dag_clone,
                    id=f"leaf-task-{idx + 1}",
                    output_type=self.output_type,
                    output_field=self.output_field,
                )
                leaf_task >> after_task

        return dag_clone

    def as_dict(self, **kwargs) -> Mapping[str, Any]:
        return {
            **super().as_dict(**kwargs),
            "input_field": self.input_field,
            "input_type": self.input_type,
            "output_field": self.output_field,
            "output_type": self.output_type,
            "job_payload": self.job_payload,
        }
