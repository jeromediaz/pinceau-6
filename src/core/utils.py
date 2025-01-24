import os
from typing import Mapping, Any, Type


def load_local_application(application_name: str):
    from core.context.global_context import GlobalContext

    GlobalContext.get_instance().applications_manager.load_local_application(
        application_name
    )


def load_dag_folder(folder: str, module_prefix: str):
    for file in os.listdir(folder):
        if file.endswith("_dag.py"):
            module_name = f"{module_prefix}.{file[:-3]}"
            __import__(module_name)


def deserialize_class(data: Mapping[str, Any]) -> Type:
    meta = data["_meta"]
    module_name = meta["module"]
    class_name = meta["class"]

    module = __import__(module_name, fromlist=[""])
    serialized_class = getattr(module, class_name)

    return serialized_class


def deserialize_instance(data: Mapping[str, Any]) -> Any:
    _class = deserialize_class(data)

    if hasattr(_class, "deserialize"):
        return _class.deserialize(data)

    raise RuntimeError(f"{_class.__name__} does not have deserialize() class method")
