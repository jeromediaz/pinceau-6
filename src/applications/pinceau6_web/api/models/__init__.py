from typing import TYPE_CHECKING

from flask import jsonify, request

from api.blueprint_decorator import register_route
from api.security_wrapper import authentication
from core.context.global_context import GlobalContext

if TYPE_CHECKING:
    from core.context.composite_context import CompositeContext
    from flask import Response


@register_route("")
@authentication()
def items(context: "CompositeContext") -> "Response":
    global_context = context.cast_as(GlobalContext)
    models_manager = global_context.models_manager

    models = []

    category_filter = request.args.get("category", "/")

    model_name_to_include = set()

    for model_description in models_manager.model_class_mapping.values():
        if any([category.startswith(category_filter) for category in model_description.categories]):
            model_name_to_include.add(model_description.name)

            parent_model = model_description.parent_model

            while parent_model:
                model_name_to_include.add(parent_model.name)
                parent_model = parent_model.parent_model

    for model_description in models_manager.model_class_mapping.values():
        if model_description.name not in model_name_to_include:
            continue

        model = [
            model_description.name,
            model_description.cls.__name__,
            model_description.cls.IS_ABSTRACT,
            model_description.parent_model.name if model_description.parent_model else None,
            model_description.model_composition()
        ]

        models.append(model)

    return jsonify(models)
