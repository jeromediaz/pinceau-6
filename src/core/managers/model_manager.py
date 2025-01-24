import importlib
import inspect
import os
from types import MappingProxyType
from typing import (
    Dict,
    AnyStr,
    Optional,
    Set,
    Sequence,
    Tuple,
    TYPE_CHECKING,
    List,
    Type,
    Mapping, Any,
)

from core.database.mongodb import MongoDBHandler
from ui.helper import ui_fields_from_base_model

if TYPE_CHECKING:
    from core.managers.dag_manager import DagManager
    from core.tasks.task_dag import TaskDAG
    from core.models.a_model import AModel
    from applications.pinceau6.models.resource_model import ResourceModel

src_base_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))


def is_model_class(cls: type) -> bool:
    if not inspect.isclass(cls):
        return False

    from core.models.a_model import AModel

    return issubclass(cls, AModel)


class ModelDescription:
    def __init__(self, name: str, cls_: Type["AModel"], **kwargs):
        self._name = name
        self._cls_: Type["AModel"] = cls_
        self._sub_models_: Set[ModelDescription] = set()
        self._flat_sub_models_: Set[ModelDescription] = set()
        self._parent_model: Optional[ModelDescription] = None
        self._categories: List[str] = [f"/data/model/{name}"]

        if "application" in kwargs:
            self._categories.append(f"/application/{kwargs['application']}")

        if "tags" in kwargs:
            self._categories.extend([f"/tag/{tag}" for tag in kwargs["tags"]])

    @property
    def name(self) -> str:
        return self._name

    @property
    def cls(self) -> Type["AModel"]:
        return self._cls_

    @property
    def sub_models(self) -> List["ModelDescription"]:
        return list(self._sub_models_)

    @property
    def is_abstract(self) -> bool:
        return self._cls_.IS_ABSTRACT

    @property
    def flat_sub_models(self) -> List["ModelDescription"]:
        return list(self._flat_sub_models_)

    @property
    def parent_model(self) -> Optional["ModelDescription"]:
        return self._parent_model

    def set_parent_model(self, parent_model: "ModelDescription") -> None:
        self._parent_model = parent_model

    def add_sub_model(self, sub_model: "ModelDescription") -> None:
        self._sub_models_.add(sub_model)

    def process_flat_sub_models(self) -> None:
        for sub_model in self._sub_models_:
            self._process_sub_model(sub_model)

    def _process_sub_model(self, sub_model: "ModelDescription") -> None:
        self._flat_sub_models_.add(sub_model)
        for sub_sub_model in sub_model.sub_models:
            self._process_sub_model(sub_sub_model)

    def _is_direct_sub_model_of(self, other_model: "ModelDescription") -> bool:
        return any((base is other_model.cls for base in self.cls.__bases__))

    @property
    def categories(self) -> List[str]:
        return self._categories

    def model_composition(self) -> Mapping[str, str]:
        ui_fields = ui_fields_from_base_model(self._cls_)
        this_level = ModelDescription.extract_model_field_from_fields(ui_fields)

        if not self._parent_model:
            return this_level


        parent_ui_fields = ui_fields_from_base_model(self._parent_model._cls_)
        parent_level = ModelDescription.extract_model_field_from_fields(parent_ui_fields)

        return {key:value for key, value in this_level.items() if key not in parent_level}

    @staticmethod
    def extract_model_field_from_fields(ui_fields: List[Mapping[str, Any]]) -> Mapping[str, str]:
        composition_map: Dict[str, str] = {}

        for ui_field in ui_fields:
            if ui_field.get('type') == 'model':
                composition_map[ui_field.get('source')] = ui_field.get('model')
            elif "fields" in ui_field:
                composition_map.update(ModelDescription.extract_model_field_from_fields(ui_field['fields']))

        return composition_map

def _filter_function(filename: AnyStr) -> bool:
    file_name, file_extension = os.path.splitext(filename)

    if file_extension != ".py" or file_name == "__init__":
        return False

    return True


class ModelsManager:
    def __init__(self) -> None:
        self._model_class_mapping: Dict[str, ModelDescription] = {}

        self.load_models_from_folder("models")

    @property
    def model_class_mapping(self) -> Mapping[str, ModelDescription]:
        return MappingProxyType(self._model_class_mapping)

    def get_model(
        self, name: str, load_from_db: bool = True
    ) -> Optional[ModelDescription]:

        model_description = self._model_class_mapping.get(name)

        if model_description:
            return model_description

        if not load_from_db:
            return None

        from core.context.global_context import GlobalContext

        global_context = GlobalContext.get_instance()

        db_handler = MongoDBHandler.from_default(global_context)

        resource_model: Optional["ResourceModel"] = db_handler.load_one(
            "resource_model", {"model_name": name}
        )

        if not resource_model:
            return None

        description = self.register_model(
            resource_model.model_name, resource_model.as_class(self)
        )

        parent_description = self.get_model(resource_model.parent_model)
        if parent_description:
            parent_description.add_sub_model(description)
            description.set_parent_model(parent_description)

            parent_description.process_flat_sub_models()

        return description

    def register_model(
        self, name: str, cls_: Type["AModel"], application: str = ""
    ) -> ModelDescription:
        description = ModelDescription(name, cls_, application=application)
        self._model_class_mapping[name] = description
        return description

    def get_model_available_dag(
        self, dag_manager: "DagManager", name: str
    ) -> Sequence[Tuple[str, bool, "TaskDAG"]]:
        results: List[Tuple[str, bool, "TaskDAG"]] = []

        # TODO: cache ?
        results.extend(dag_manager.model_to_dag_list_map.get(name, []))

        model_description = self._model_class_mapping.get(name)
        if model_description:
            parent_model = model_description.parent_model

            while parent_model is not None:
                results.extend(
                    dag_manager.model_to_dag_list_map.get(parent_model.name, [])
                )
                parent_model = parent_model.parent_model

        return results

    def _load_models_from_module(
        self, module_prefix: str, used_module_name: str, application: str = ""
    ):
        full_module_name = f"{module_prefix}.{used_module_name}"

        try:
            module = importlib.import_module(full_module_name)
        except ModuleNotFoundError as e:
            raise RuntimeError(f"Error loading module {full_module_name}") from e

        class_members = inspect.getmembers(module, is_model_class)

        for cls_name, cls_ in class_members:
            if hasattr(cls_, "META_MODEL"):
                model_name = getattr(cls_, "META_MODEL")

                self.register_model(model_name, cls_, application)

    def load_models_from_folder(
        self, folder_path: AnyStr | os.PathLike[AnyStr], application: str = ""
    ) -> None:
        for dir_path, dir_names, filenames in os.walk(folder_path):
            relative_path = os.path.relpath(str(dir_path), src_base_folder)

            current_folder = os.path.basename(os.path.normpath(dir_path))
            if current_folder == "__pycache__":
                # we can skip pycache folder
                continue

            filtered_filenames = filter(_filter_function, filenames)

            module_names = map(
                lambda filename: os.path.splitext(filename)[0], filtered_filenames
            )

            module_prefix = str(relative_path).replace(os.path.sep, ".")

            for module_name in module_names:
                if isinstance(module_name, bytes):
                    used_module_name = module_name.decode()
                else:
                    used_module_name = module_name

                self._load_models_from_module(
                    module_prefix, used_module_name, application=application
                )

        self._build_models_inheritance()

    def _build_models_inheritance(self) -> None:
        for model in self._model_class_mapping.values():
            for other_model in self._model_class_mapping.values():
                if model == other_model:
                    continue
                if other_model._is_direct_sub_model_of(model):
                    model.add_sub_model(other_model)
                    other_model.set_parent_model(model)

        for model in self._model_class_mapping.values():
            model.process_flat_sub_models()
