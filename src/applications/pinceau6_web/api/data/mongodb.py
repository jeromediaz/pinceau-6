from typing import TYPE_CHECKING, Tuple

from bson import ObjectId
from flask import jsonify, request, abort, Response
from pydantic import ValidationError

from api.blueprint_decorator import register_route, action_required
from api.helpers import get_filters, get_range
from api.security_wrapper import authentication
from applications.chat.models.a_chat import AChat
from applications.chat.models.chat_dag_for_object import ChatDagForObject
from core.database.mongodb import MongoDBHandler
from core.models.types import ModelUsageMode
from misc.mongodb_helper import mongodb_collection
from misc.pydantic_helper import flask_abort_pydantic_error
from ui.helper import available_dag_for_model

if TYPE_CHECKING:
    from core.context.composite_context import CompositeContext


@register_route(
    "/mongodb/<string:collection>", endpoint="mongodb_post", methods=["POST"]
)
@authentication()
@action_required("DataCreate", "data/mongodb/<collection>")
def mongodb_post_collection_object(
    collection: str, context: "CompositeContext"
) -> Response | Tuple[Response, int]:

    new_object = request.get_json()
    if not new_object:
        abort(400)

    model_name = new_object.get("_meta", {}).get(
        "model"
    )  # TODO: security if model isn't a subclass of definition

    if not model_name:
        abort(400)

    model_definition = context.models_manager.get_model(model_name)

    if not model_definition:
        abort(404)

    model_class = model_definition.cls
    if model_class.IS_ABSTRACT:
        abort(403)

    try:
        model_class_object = model_class(**new_object)

        MongoDBHandler.from_default(context).save_object(
            context, model_class_object, collection
        )

        return jsonify(
            model_class_object.to_json_dict(display_mode=ModelUsageMode.SHOW)
        )
    except ValidationError as e:
        flask_abort_pydantic_error(e)


@register_route(
    "/mongodb/<string:collection>", endpoint="mongodb_list", methods=["GET"]
)
@authentication()
@action_required("DataList", "data/mongodb/<collection>")
def mongodb_list_collection(collection: str, context: "CompositeContext") -> Response:

    db_handler = MongoDBHandler.from_default(context)

    start, end = get_range()

    filter_arg_object = get_filters()

    (start, end, total_count), items = db_handler.search(
        collection, start=start, end=end, filters=filter_arg_object
    )
    response = jsonify(items)
    response.headers.add("Content-Range", f"graphs {start}-{end}/{total_count}")

    return response


@register_route(
    "/mongodb/<string:collection>/<string:object_id>",
    endpoint="mongodb_delete",
    methods=["DELETE"],
)
@authentication()
@action_required("DataDelete", "data/mongodb/<collection>/<object_id>")
def mongodb_delete_collection_object(
    collection: str, object_id: str, context: "CompositeContext"
) -> Response:

    MongoDBHandler.from_default(context).delete_object(context, object_id, collection)

    return jsonify({})


@register_route(
    "/mongodb/<string:collection>/<string:object_id>",
    endpoint="mongodb_put",
    methods=["PUT"],
)
@authentication()
@action_required("DataEdit", "data/mongodb/<collection>/<object_id>")
def mongodb_put_collection_object(
    collection: str, object_id: str, context: "CompositeContext"
) -> Response | Tuple[Response, int]:
    json_data = request.get_json()

    if not json_data or not isinstance(json_data, dict):
        raise ValueError("No json data provided")

    if "_id" not in json_data:
        json_data["_id"] = object_id
    elif json_data["_id"] != object_id:
        # mismatching ID
        abort(400)

    try:
        old_object_value = MongoDBHandler.from_default(context).load_one(
            collection, {"_id": object_id}
        )

        # TODO: perform permission validation
        if not old_object_value:
            abort(404)
            # .get_object(context, object_id))

        new_value = old_object_value.as_dict(mode="python")
        new_value.update(json_data)

        data_object = MongoDBHandler.load_object(new_value)
        # TODO: load previous value, then merge with json_data

        MongoDBHandler.from_default(context).update_object(
            context, data_object, collection
        )

    except ValidationError as e:
        flask_abort_pydantic_error(e)

    return jsonify({})


@register_route(
    "/mongodb/<string:collection>/<string:object_id>",
    endpoint="mongodb_get",
    methods=["GET"],
)
@authentication()
@action_required("DataShow", "data/mongodb/<collection>/<object_id>")
def mongodb_get_collection_object(
    collection: str, object_id: str, context: "CompositeContext"
) -> Response:
    mongo_collection = mongodb_collection(context, "mongodb", "pinceau6", collection)

    value = mongo_collection.find_one({"_id": ObjectId(object_id)})

    model_object = MongoDBHandler.load_object(value).to_json_dict(
        display_mode=ModelUsageMode.SHOW
    )

    return jsonify(model_object)


@register_route(
    "/mongodb/<string:collection>/<string:object_id>/chat/<string:dag_variant_id>",
    endpoint="mongodb_collection_chat_object",
)
@authentication()
@action_required("chat", "data/mongodb/<collection>/<object_id>/chat/<dag_variant_id>")
def mongodb_get_collection_chat_object(
    collection: str, object_id: str, dag_variant_id: str, context: "CompositeContext"
) -> Response:
    from core.context.global_context import GlobalContext

    mongo_collection = mongodb_collection(context, "mongodb", "pinceau6", collection)

    value = mongo_collection.find_one({"_id": ObjectId(object_id)})

    if not value:
        abort(404, "Value not found")

    model_object = MongoDBHandler.load_object(value)

    model_definition = context.models_manager.get_model(model_object.model)

    if not model_definition:
        abort(404, "Model not found")

    global_context = context.cast_as(GlobalContext)

    available_dag_list = available_dag_for_model(model_definition.name, global_context)

    filter_available_dag = (
        obj for obj in available_dag_list if obj[2].id == dag_variant_id
    )

    single_available_dag = next(filter_available_dag, None)

    if not single_available_dag:
        abort(404, "dag not found")

    db_handler = MongoDBHandler.from_default(context)

    start, end = get_range()

    model_description = global_context.models_manager.get_model(
        ChatDagForObject.META_MODEL
    )
    allowed_models = [ChatDagForObject.META_MODEL]
    if model_description:
        for sub_model in model_description.flat_sub_models:
            allowed_models.append(sub_model.name)

    (start, end, total_count), items = db_handler.search(
        AChat.META_MODEL, start=start, end=end, filters={"_meta.model": allowed_models}
    )
    response = jsonify(items)
    response.headers.add("Content-Range", f"graphs {start}-{end}/{total_count}")

    return response
