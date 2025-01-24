from typing import TYPE_CHECKING, Tuple

from flask import jsonify, request, abort, Response
from pydantic import ValidationError

from api.blueprint_decorator import register_route
from api.helpers import get_filters, get_range
from api.security_wrapper import authentication
from core.database.elasticsearch import EsIndexHandler
from core.database.mongodb import MongoDBHandler
from core.models.types import ModelUsageMode
from misc.pydantic_helper import flask_abort_pydantic_error

if TYPE_CHECKING:
    from core.context.composite_context import CompositeContext


@register_route(
    "/elastic/<string:collection>", endpoint="elastic_post", methods=["POST"]
)
@authentication()
def elastic_post_collection_object(
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
    "/elastic/<string:collection>", endpoint="elastic_list", methods=["GET"]
)
@authentication()
def elastic_list_collection(collection: str, context: "CompositeContext") -> Response:
    db_handler = EsIndexHandler.from_default(context, index=collection)

    start, end = get_range()

    filter_arg_object = get_filters()

    (start, end, total_count), items = db_handler.search(
        collection, start=start, end=end, filters=filter_arg_object
    )
    response = jsonify(items)
    response.headers.add("Content-Range", f"graphs {start}-{end}/{total_count}")

    return response


@register_route(
    "/elastic/<string:collection>/<string:object_id>",
    endpoint="elastic_delete",
    methods=["DELETE"],
)
@authentication()
def elastic_delete_collection_object(
    collection: str, object_id: str, context: "CompositeContext"
) -> Response:

    MongoDBHandler.from_default(context).delete_object(context, object_id, collection)

    return jsonify({})


@register_route(
    "/elastic/<string:collection>/<string:object_id>",
    endpoint="elastic_put",
    methods=["PUT"],
)
@authentication()
def elastic_put_collection_object(
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
        data_object = MongoDBHandler.load_object(json_data)
        MongoDBHandler.from_default(context).update_object(
            context, data_object, collection
        )

    except ValidationError as e:
        flask_abort_pydantic_error(e)

    return jsonify({})


@register_route(
    "/elastic/<string:collection>/<string:object_id>",
    endpoint="elastic_get",
    methods=["GET"],
)
@authentication()
def elastic_get_collection_object(
    collection: str, object_id: str, context: "CompositeContext"
) -> Response:

    db_handler = EsIndexHandler.from_default(context, index=collection)

    item = db_handler.load_one({"_id": object_id}, as_model="amodel")

    response = jsonify(item.to_json_dict())

    return response
