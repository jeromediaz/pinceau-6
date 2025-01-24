from typing import TYPE_CHECKING

from flask import jsonify, Response

from api.blueprint_decorator import register_route
from api.security_wrapper import authentication

if TYPE_CHECKING:
    from core.context.composite_context import CompositeContext


@register_route("/me")
@authentication()
def user_me(context: "CompositeContext") -> Response:

    user_object = context.user

    if not user_object:
        return jsonify({"status": "KO"})

    return jsonify({"status": "OK", "data": user_object.to_json_dict()})
