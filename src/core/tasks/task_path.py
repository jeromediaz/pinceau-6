from typing import Iterable, TYPE_CHECKING

from core.tasks.task_data import TaskDataContract

if TYPE_CHECKING:
    from core.tasks.task_dag import TaskDAG


class TaskPath:
    def __init__(self, *node: str):
        self.node_list: list[str] = list(node)

    def add_node(self, node: str):
        self.node_list.append(node)

    def prepend_node(self, node: str):
        self.node_list.insert(0, node)

    def __str__(self):
        return " > ".join(self.node_list)

    def process_first_node(self, dag: "TaskDAG") -> Iterable["TaskPath"]:
        first_node_id = self.node_list[0]
        first_node = dag.task_node_map[first_node_id]
        print(f"{first_node_id=} {first_node.parent_nodes=}")
        if first_node and first_node.parent_nodes:
            first_parent_node = first_node.parent_nodes[0]

            for parent_node in first_node.parent_nodes[1:]:
                task_path = TaskPath(*self.node_list)
                task_path.prepend_node(parent_node.from_id)
                yield task_path

            self.prepend_node(first_parent_node.from_id)
            yield self

    def process_last_node(self, dag: "TaskDAG") -> Iterable["TaskPath"]:
        last_node_id = self.node_list[-1]
        last_node = dag.task_node_map[last_node_id]
        if last_node and last_node.sub_nodes:
            first_sub_node = last_node.sub_nodes[0]

            for sub_node in last_node.sub_nodes[1:]:
                task_path = TaskPath(*self.node_list)
                task_path.add_node(sub_node.to_id)

                yield task_path

            self.add_node(first_sub_node.to_id)
            yield self

    def get_required_inputs(self, dag) -> TaskDataContract:
        print(f"{self}")
        contract = dag.task_node_map[self.node_list[-1]].task.required_inputs()

        provided_outputs = [
            dag.task_node_map[self.node_list[0]].task.provided_outputs()
        ]
        for node_id in self.node_list[1:]:
            provided_outputs.append(
                dag.task_node_map[node_id].task.provided_outputs(provided_outputs[-1])
            )

        for index, node_id in reversed(list(enumerate(self.node_list[:-1]))):
            node = dag.task_node_map[node_id]
            contract.subtract_all(provided_outputs[index])
            contract.add_all(node.task.required_inputs())
            # TODO: add contract exception

        return contract
