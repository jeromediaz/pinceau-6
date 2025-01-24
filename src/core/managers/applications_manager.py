import os
import weakref
from typing import (
    Dict,
    TYPE_CHECKING, Optional,
)

from api import register_blueprints
from core.utils import load_dag_folder

if TYPE_CHECKING:
    from core.context.global_context import GlobalContext

src_base_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))


class ApplicationsManager:
    def __init__(self, global_context: "GlobalContext") -> None:
        self._applications_to_folder_loaded: Dict[str, str] = {}
        self._application_tag_name_map: Dict[str, str] = {}
        self._global_context = weakref.ref(global_context)

    def load_local_application(self, application_key: str, application_name: Optional[str]=None):
        application_name = application_name or application_key
        application_category = f"/application/{application_key}"

        folder = f"applications/{application_key}"
        module_prefix = f"applications.{application_key}"

        load_dag_folder(folder, module_prefix)

        global_context = self._global_context()
        if global_context is None:
            raise RuntimeError("Global context has been deallocated")

        global_context.models_manager.load_models_from_folder(
            folder + "/models", application_key
        )

        self._applications_to_folder_loaded[application_key] = folder
        self._application_tag_name_map[application_category] = application_name

        websocket_manager = self._global_context().websocket_manager

        if websocket_manager:
            websocket_manager.register_handlers_in_folder(
                f"{module_prefix}.websockets", os.path.join(folder, "websockets")
            )

        if global_context.flask_app:
            api_json_file = os.path.join(folder, "api", "api.json")
            print(api_json_file)
            if os.path.exists(api_json_file):
                with open(api_json_file, "r") as f:
                    import json
                    blueprints = json.load(f)
                    print(blueprints)
                    register_blueprints(global_context.flask_app, f"{module_prefix}.api", blueprints)

                print(global_context.flask_app.url_map)

    @property
    def tag_name_map(self) -> Dict[str, str]:
        return self._application_tag_name_map