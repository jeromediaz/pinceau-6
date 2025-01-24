from typing import Mapping, Any

from core.tasks.graph_element import GraphElement
from misc.functions import extract_dag_id


class GraphElementWithParameters(GraphElement):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._params = kwargs

    def _params_for_dag_and_key(self, dag_id: str, key: str) -> Mapping[str, Any]:
        dag_identifier, dag_variant, _ = extract_dag_id(dag_id)

        from core.context.global_context import GlobalContext

        global_context = GlobalContext.get_instance()
        parameters = global_context.dag_manager.get_dag_task_parameters(
            dag_identifier, dag_variant
        ).get(key, {})

        return {**parameters, **self._params}
