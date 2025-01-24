from typing import TYPE_CHECKING

from flask import Response, abort, jsonify, request

from api.blueprint_decorator import register_route
from api.security_wrapper import authentication
from core.models.types import ModelUsageMode
from misc.functions import check_if_dag_chat_compatible
from ui.helper import available_dag_for_model

if TYPE_CHECKING:
    from core.context.composite_context import CompositeContext


@register_route("/schema/<string:model>", endpoint="mongodb_schema")
@authentication()
def model_schema(model: str, context: "CompositeContext") -> Response:
    mode = request.args.get("mode", "default").lower()

    display_mode = ModelUsageMode(mode)

    model_definition = context.models_manager.get_model(model)

    if not model_definition:
        abort(404, "Model not found")

    model_class = model_definition.cls

    from core.context.global_context import GlobalContext

    global_context = context.cast_as(GlobalContext)

    available_dag_list = available_dag_for_model(model_definition.name, global_context)

    dag_actions = []
    chat_actions = []
    for field_name, is_multiple, dag in available_dag_list:
        inputs = [
            {"source": key, **value}
            for key, value in dag.get_required_inputs().fields_map().items()
            if key != field_name
        ]

        dag_chat_compatible = check_if_dag_chat_compatible(dag, ignore_field=field_name)
        if dag_chat_compatible:
            chat_actions.append(
                {
                    "name": dag.id,
                    "input": dag_chat_compatible.input_key,
                    "output": dag_chat_compatible.output_key,
                    "field": field_name,
                }
            )

        dag_actions.append(
            {
                "name": dag.id,
                "multiple": is_multiple,
                "field": field_name,
                "inputs": inputs,
            }
        )

    return_value = {
        "name": model_definition.name,
        "isAbstract": model_class.IS_ABSTRACT,
        "fields": model_class.ui_model_fields(display_mode=display_mode),
        "layout": model_class.ui_model_layout(),
        "subModels": [
            definition.name
            for definition in model_definition.sub_models
            if not definition.is_abstract
        ],
        "dagActions": dag_actions,
        "chatActions": chat_actions,
        "categories": model_definition.categories,
    }

    return jsonify(return_value)
