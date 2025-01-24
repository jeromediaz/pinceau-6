import weakref
from typing import (
    Mapping,
    Sequence,
    Optional,
    Tuple,
    Dict,
    List,
    TYPE_CHECKING,
    Any,
    cast,
)

from bson import ObjectId

from conf import Config
from conf.config import RunMode
from core.managers.graph_element_manager import GraphElementManager
from core.tasks.task_dag import TaskDAG
from misc.functions import strtobool, extract_dag_id, construct_dag_id
from misc.mongodb_helper import mongodb_collection

ModelToDAGMapping = Mapping[str, Sequence[Tuple[str, bool, TaskDAG]]]

if TYPE_CHECKING:
    from core.context.global_context import GlobalContext
    from models.dag_persisted_model import DAGPersistedModel
    from core.callbacks.dag_execution_memory import DagExecutionMemory


class DagManager(GraphElementManager[TaskDAG]):

    def __init__(self, global_context: "GlobalContext") -> None:
        super().__init__()
        self._model_to_dag_list_map: Optional[ModelToDAGMapping] = None
        self._persisted_models_map: Optional[Dict[str, List["DAGPersistedModel"]]] = (
            None
        )
        self._persisted_models_list: Optional[List["DAGPersistedModel"]] = None

        # TODO: load from database

        self._global_context = weakref.ref(global_context)
        self._dag_execution_memory_map: Dict[str, "DagExecutionMemory"] = {}
        self._dag_task_parameters: Optional[Dict[str, Mapping[str, Any]]] = None
        self._dag_variants: Optional[Dict[str, List[str]]] = None
        self._dag_variant_ids: Optional[Dict[str, ObjectId]] = None

    @property
    def dag_variants(self) -> Dict[str, List[str]]:
        self._fetch_variant_params()

        return cast(Dict[str, List[str]], self._dag_variants)

    @property
    def dag_variant_ids(self) -> Dict[str, ObjectId]:
        self._fetch_variant_params()

        return cast(Dict[str, ObjectId], self._dag_variant_ids)

    @property
    def dag_task_parameters(self) -> Dict[str, Mapping[str, Any]]:
        self._fetch_variant_params()

        return cast(Dict[str, Mapping[str, Any]], self._dag_task_parameters)

    def _fetch_variant_params(self) -> None:

        if self._dag_task_parameters is not None and self._dag_variants is not None:
            return

        self._dag_task_parameters = {}
        self._dag_variants = {}
        self._dag_variant_ids = {}

        raw_value = Config().get("LOAD_PERSIST_MODELS", default="True")

        if not strtobool(raw_value):
            return

        config = Config()
        if config.run_mode == RunMode.TEST:
            return

        from core.context.global_context import GlobalContext

        context = GlobalContext.get_instance()
        mongo_collection = mongodb_collection(
            context, "mongodb", "pinceau6", "_dag_params"
        )

        cursor = mongo_collection.find({})

        self._dag_variants = {}

        for row in cursor:
            row_variant_id = row["variant_id"]
            row_variant = row["variant"]
            row_dag_id = row["dag_id"]
            row_params = row["params"]
            self._dag_task_parameters[row_variant_id] = row_params
            self._dag_variants.setdefault(row_dag_id, []).append(row_variant)
            self._dag_variant_ids[row_variant_id] = row["_id"]

            if (
                row_variant_id not in context.dag_manager
                and row_dag_id in context.dag_manager
            ):
                context.dag_manager[row_dag_id].clone(row_variant_id)

    def _fetch_single_variant_params(self, dag_id: str, variant_id: str):
        if self._dag_task_parameters is not None or self._dag_variants is not None:
            return

        self._dag_task_parameters = {}
        self._dag_variants = {}
        self._dag_variant_ids = {}

        from core.context.global_context import GlobalContext

        context = GlobalContext.get_instance()
        mongo_collection = mongodb_collection(
            context, "mongodb", "pinceau6", "_dag_params"
        )

        data = mongo_collection.find_one({"dag_id": dag_id, "variant": variant_id})

        if not data:
            return

        row_variant_id = data["variant_id"]
        row_variant = data["variant"]
        row_dag_id = data["dag_id"]
        row_params = data["params"]
        row_id = data["_id"]

        self._dag_task_parameters[row_variant_id] = row_params
        variants = self._dag_variants.setdefault(row_dag_id, [])
        if row_variant not in variants:
            variants.append(row_variant)

        self._dag_variant_ids[row_variant_id] = row_id

        if (
            row_variant_id not in context.dag_manager
            and row_dag_id in context.dag_manager
        ):
            context.dag_manager[row_dag_id].clone(row_variant_id)

    def get_dag_variants(self, dag_id: str):
        dag_variants = self.dag_variants

        if dag_id not in dag_variants:
            dag_variants[dag_id] = ["_default_"]
            return ["_default_"]

        variants = dag_variants[dag_id]
        if "_default_" not in variants:
            variants.insert(0, "_default_")

        return variants

    def remove_dag_task_parameters(self, dag_id: str, variant: str):
        from core.context.global_context import GlobalContext

        context = GlobalContext.get_instance()
        mongo_collection = mongodb_collection(
            context, "mongodb", "pinceau6", "_dag_params"
        )

        mongo_collection.delete_one({"dag_id": dag_id, "variant": variant})

        variant_id = dag_id if variant == "_default_" else f"{dag_id}[{variant}]"

        self._map.pop(variant_id, None)

        dag_variant_ids = self._dag_variant_ids
        if dag_variant_ids:
            dag_variant_ids.pop(variant_id, None)

        dag_variants: Dict[str, List[str]] = (
            self._dag_variants if self._dag_variants else {}
        )
        if dag_variants:
            dag_variants[dag_id] = [
                local_variant
                for local_variant in dag_variants
                if local_variant != variant
            ]

    def set_dag_task_parameters(
        self, dag_id: str, variant: str, params: Mapping[str, Any]
    ):
        variant_id = dag_id if variant == "_default_" else f"{dag_id}[{variant}]"

        full_data = {
            "variant_id": variant_id,
            "dag_id": dag_id,
            "variant": variant,
            "params": params,
        }

        dag_task_parameters = self.dag_task_parameters

        from core.context.global_context import GlobalContext

        context = GlobalContext.get_instance()
        mongo_collection = mongodb_collection(
            context, "mongodb", "pinceau6", "_dag_params"
        )

        dag_variant_ids = self.dag_variant_ids
        dag_variants = self.dag_variants

        if variant_id in dag_variant_ids:
            mongo_id = dag_variant_ids[variant_id]
            mongo_collection.update_one({"_id": mongo_id}, {"$set": full_data})

        else:
            param_object = mongo_collection.find_one({"variant_id": variant_id})

            if param_object:
                mongo_id = param_object["_id"]
                mongo_collection.update_one({"_id": mongo_id}, {"$set": full_data})

            else:
                result = mongo_collection.insert_one(full_data)
                mongo_id = result.inserted_id

                context.dag_manager[dag_id].clone(variant_id)

            dag_variant_ids[variant_id] = mongo_id

        variants = dag_variants.setdefault(dag_id, [])
        if variant not in variants:
            variants.append(variant)

        dag_task_parameters[variant_id] = params

    def get_dag_task_parameters(self, dag_id: str, variant: str) -> Mapping[str, Any]:
        self._fetch_variant_params()

        variant_id = construct_dag_id(dag_id, variant)

        dag_task_parameters = self.dag_task_parameters

        if variant_id in dag_task_parameters:
            return dag_task_parameters[variant_id]

        self._fetch_single_variant_params(dag_id, variant)

        if variant_id in dag_task_parameters:
            return dag_task_parameters[variant_id]

        if variant != "_default_" and dag_id not in dag_task_parameters:
            return dag_task_parameters.get(dag_id, {})

        return {}

    def _fetch_persisted_models(self):

        config = Config()

        self._persisted_models_list = []
        self._persisted_models_map = {}

        raw_value = config.get("LOAD_PERSIST_MODELS", default="True")

        if not strtobool(raw_value):
            return

        from core.database.mongodb import MongoDBHandler

        db_handler = MongoDBHandler.from_default(self._global_context())

        persisted_models = db_handler.load_multiples("dag_persisted", {})

        for persisted_model in persisted_models:
            parent_dag_id = persisted_model.parent_dag_id
            self._persisted_models_list.append(persisted_model)

            persisted_dag_parent_list = self._persisted_models_map.setdefault(
                parent_dag_id, list()
            )

            persisted_dag_parent_list.append(persisted_model)

    @property
    def persisted_models_map(self) -> Mapping[str, List["DAGPersistedModel"]]:
        if self._persisted_models_map is None:
            self._fetch_persisted_models()

        if self._persisted_models_map is None:
            raise ValueError("DagManager has no persisted models")

        return self._persisted_models_map.copy()

    @property
    def persisted_models_list(self) -> Sequence["DAGPersistedModel"]:
        if self._persisted_models_list is None:
            self._fetch_persisted_models()

        if self._persisted_models_list is None:
            raise ValueError("DagManager has no persisted models")

        return self._persisted_models_list.copy()

    def get(self, id_: str) -> Optional["TaskDAG"]:
        if id_ not in self._map:
            dag_identifier, dag_variant, job_id = extract_dag_id(id_)

            dag_id = construct_dag_id(dag_identifier, dag_variant)

            if dag_id in self._map:
                self._map[dag_id].clone(id_)

            elif dag_identifier in self._map:
                self._map[dag_identifier].clone(id_)

        return self._map.get(id_)

    def __getitem__(self, dag_id: str) -> "TaskDAG":
        found_dag = self.get(dag_id)

        if not found_dag:
            raise ValueError(f"No DAG Found for id {dag_id}")

        return found_dag

    def __setitem__(self, key, value):
        self._model_to_dag_list_map = None
        super().__setitem__(key, value)

        if value is None:
            return

        persisted_models_map = self.persisted_models_map

        self._fetch_variant_params()
        if key in self._dag_variants:
            for variant in self._dag_variants[key]:
                if variant == "_default_":
                    continue

                variant_id = f"{key}[{variant}]"
                if variant_id in self._dag_task_parameters:
                    value.clone(variant_id)

        if key in persisted_models_map:
            for persisted_dag_model in persisted_models_map[key]:
                dag_id = persisted_dag_model.dag_id

                task_dag = self.get(key)
                task_dag.clone(dag_id)

    def __delitem__(self, key):
        super().__delitem__(key)
        self._dag_execution_memory_map.pop(key, None)
        self._model_to_dag_list_map = None

    def has_memory(self, key) -> bool:
        return key in self._dag_execution_memory_map

    def get_memory(self, key) -> "DagExecutionMemory":
        if key not in self._dag_execution_memory_map:
            from core.callbacks.dag_execution_memory import DagExecutionMemory

            memory = DagExecutionMemory(key)
            self._dag_execution_memory_map[key] = memory

            dag = self.get(key)

            if dag is not None:
                ui_elements = []
                for node in dag.task_node_map.values():
                    ui_elements += node.task.get_ui()
                memory.set_ui_elements(ui_elements)

        return self._dag_execution_memory_map[key]

    def scheduled_persisted_dag_models(self) -> List["DAGPersistedModel"]:
        return list(
            filter(
                lambda persisted_model: persisted_model.scheduler is not None,
                self.persisted_models_list,
            )
        )

    @property
    def model_to_dag_list_map(self) -> ModelToDAGMapping:
        if self._model_to_dag_list_map is not None:
            return self._model_to_dag_list_map

        new_value: Dict[str, List[Tuple[str, bool, TaskDAG]]] = {}
        for name, dag in self._map.items():
            if dag.job_id:
                # we want only DAG and variants, not jobs
                continue

            required_inputs = dag.get_required_inputs().fields_map()

            required_reference_inputs = {
                key: value
                for key, value in required_inputs.items()
                if value.get("type", "") == "reference"
            }

            if len(required_reference_inputs) != 1:
                # only DAG with a single reference input can be used
                continue

            single_input_name, single_input_value = next(
                iter(required_reference_inputs.items())
            )

            if single_input_value.get("type", "") != "reference":
                continue

            reference_value = cast(str, single_input_value.get("reference"))
            model_value = single_input_value.get("model")
            multiple_value = single_input_value.get("multiple", False)

            # remove data/mongodb/ prefix
            # TODO: handle cases where it isn't coming from mongo
            mongo_model_name = model_value if model_value else reference_value[13:]
            model_type = new_value.setdefault(mongo_model_name, [])
            model_type.append((single_input_name, multiple_value, dag))

        self._model_to_dag_list_map = new_value

        return self._model_to_dag_list_map
