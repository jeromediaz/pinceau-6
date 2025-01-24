from inspect import getmembers
from typing import Mapping, Any

from flask import Blueprint

from api.blueprint_decorator import is_register_route

api_blueprint = Blueprint("api", __name__, url_prefix="/api/1.0/")



def register_blueprints(app, module_prefix: str, blueprints: Mapping[str, Any], **kwargs):
    blueprint_api = Blueprint(module_prefix.replace('.', '_'), __name__, **kwargs)

    for module, blueprints_data in blueprints.items():
        module_name = f"{module_prefix}.{module}"
        module = __import__(module_name, fromlist=[""])
        functions = getmembers(module, is_register_route)

        if not functions:
            continue

        if not isinstance(blueprints_data, list):
            blueprints_data = [blueprints_data]

        for blueprint_data in blueprints_data:
            if isinstance(blueprint_data, str):
                blueprint_data = {"blueprint_kwargs": {"url_prefix": blueprint_data}}

            blueprint_name = blueprint_data.get(
                "blueprint_name", module.__name__.split(".")[-1]
            )
            blueprint_kwargs = blueprint_data.get("blueprint_kwargs", {})
            params = blueprint_data.get("params", {})
            module_blueprint = Blueprint(blueprint_name, module.__name__)

            print(blueprint_name)

            for register_route in functions:
                register_route[1](module_blueprint, **params)

            blueprint_api.register_blueprint(module_blueprint, **blueprint_kwargs)

    #if module_prefix == "api":
    app.register_blueprint(blueprint_api, **kwargs)
