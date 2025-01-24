from typing import TYPE_CHECKING, Optional, List, Mapping, Any

from core.tasks.types import TaskEdgeKind, ProcessMode
from core.utils import deserialize_instance

if TYPE_CHECKING:
    from core.tasks.task import Task
    import pydot


class TaskEdge:
    def __init__(
        self, from_id: str, to_id: str, edge_type: TaskEdgeKind = TaskEdgeKind.DEFAULT
    ):
        self._from_id = from_id
        self._to_id = to_id
        self._type = edge_type

    def serialize(self) -> Mapping[str, Any]:
        return {"from_id": self._from_id, "to_id": self._to_id, "type": self._type.name}

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> "TaskEdge":
        from_id = data["from_id"]
        to_id = data["to_id"]
        edge_type = data["type"]

        return TaskEdge(from_id, to_id, getattr(TaskEdgeKind, edge_type))

    def __str__(self) -> str:
        return f"{self._from_id} -> {self._to_id} ({self._type})"

    def clone(self) -> "TaskEdge":
        return TaskEdge(self._from_id, self._to_id, self._type)

    @property
    def from_id(self) -> str:
        return self._from_id

    @property
    def to_id(self) -> str:
        return self._to_id

    @property
    def type(self) -> TaskEdgeKind:
        return self._type

    def as_json(self) -> List[str]:
        return [self._from_id, self._to_id, self._type.name]

    def as_dot_edge(self) -> "pydot.Edge":
        import pydot

        edge_attributes = {}

        if self.type in {TaskEdgeKind.DEFAULT, TaskEdgeKind.DIRECT}:
            pass
        elif self.type == TaskEdgeKind.CONDITIONAL:
            edge_attributes["samehead"] = "conditional"
            edge_attributes["tailhead"] = "odot"
            edge_attributes["style"] = "dotted"
        elif self.type == TaskEdgeKind.LOOP:
            edge_attributes["samehead"] = "start"
            edge_attributes["style"] = "dashed"
        elif self.type == TaskEdgeKind.LOOP_START:
            edge_attributes["samehead"] = "start"
            edge_attributes["tailhead"] = "odiamond"
        elif self.type == TaskEdgeKind.LOOP_END:
            edge_attributes["samehead"] = "end"
            edge_attributes["tailhead"] = "diamond"

        return pydot.Edge(self.from_id, self._to_id, **edge_attributes)


class TaskNode:
    def __init__(self, dag_id: str, task: "Task"):
        self.sub_nodes: list[TaskEdge] = []
        self.parent_nodes: list[TaskEdge] = []
        self.task: "Task" = task
        self.dag_id = dag_id

    def clone(self, dag_id: str, task_id: Optional[str]) -> "TaskNode":
        new_node = TaskNode(dag_id, self.task.clone(id=task_id))

        new_node.sub_nodes = [edge.clone() for edge in self.sub_nodes]
        new_node.parent_nodes = [edge.clone() for edge in self.parent_nodes]

        return new_node

    def serialize(self) -> Mapping[str, Any]:
        return {
            "dag_id": self.dag_id,
            "task": self.task.serialize(),
            "sub_nodes": [edge.serialize() for edge in self.sub_nodes],
            "parent_nodes": [edge.serialize() for edge in self.parent_nodes],
        }

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> "TaskNode":
        task_data = data["task"]
        sub_nodes_data = data["sub_nodes"]
        parent_nodes_data = data["parent_nodes"]
        dag_id = data["dag_id"]

        instance = cls(dag_id, deserialize_instance(task_data))

        instance.sub_nodes = [
            TaskEdge.deserialize(edge_data) for edge_data in sub_nodes_data
        ]
        instance.parent_nodes = [
            TaskEdge.deserialize(edge_data) for edge_data in parent_nodes_data
        ]

        return instance

    def get_dag(self) -> str:
        return self.dag_id

    def add_sub_node(self, node: str, edge_type: TaskEdgeKind = TaskEdgeKind.DEFAULT):

        if edge_type == TaskEdgeKind.DEFAULT:
            if self.task.process_mode == ProcessMode.GENERATOR:
                edge_type = TaskEdgeKind.LOOP

            elif self.task.is_conditional_out:
                edge_type = TaskEdgeKind.CONDITIONAL
            else:
                edge_type = TaskEdgeKind.DIRECT

        self.sub_nodes.append(TaskEdge(self.task.id, node, edge_type=edge_type))

    def add_parent_node(
        self, node: str, edge_type: TaskEdgeKind = TaskEdgeKind.DEFAULT
    ):
        self.parent_nodes.append(TaskEdge(node, self.task.id, edge_type=edge_type))

    def add_to_graph(self, graph: "pydot.Dot"):
        import pydot

        label = f'<<table border="0" cellborder="0" cellspacing="0" cellpadding="4"><tr> <td><b class="task-name">{self.task.label}</b><br/><i class="task-status-label">-</i></td> </tr></table>>'

        graph.add_node(
            pydot.Node(
                self.task.id,
                obj_dict={
                    "name": self.task.id,
                    "type": "node",
                    "attributes": {
                        "shape": "rect",
                        "id": self.task.id,
                        "label": label,
                        "width": 2,
                    },
                },
            )
        )

        for sub_node in self.sub_nodes:
            graph.add_edge(sub_node.as_dot_edge())

    def usable_sub_nodes(
        self, for_mode: TaskEdgeKind = TaskEdgeKind.DEFAULT
    ) -> List[TaskEdge]:
        if for_mode == TaskEdgeKind.DEFAULT:
            return [
                sub_node
                for sub_node in self.sub_nodes
                if sub_node.type
                in {TaskEdgeKind.DIRECT, TaskEdgeKind.CONDITIONAL, TaskEdgeKind.LOOP}
            ]

        return [sub_node for sub_node in self.sub_nodes if sub_node.type == for_mode]
