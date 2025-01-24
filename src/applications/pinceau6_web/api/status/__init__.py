from flask import jsonify, Response

from api.blueprint_decorator import register_route


@register_route("/", enabled=lambda **params: params.get("version", 1) > 1)
def status(*, version: int = 1) -> Response:

    return jsonify({"status": "OK", "version": version})
