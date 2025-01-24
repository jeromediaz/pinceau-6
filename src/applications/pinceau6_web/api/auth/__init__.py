import jwt
from flask import jsonify, request

from api.blueprint_decorator import register_route
from core.context.global_context import GlobalContext
from core.database.mongodb import MongoDBHandler


@register_route("/login", endpoint="login", methods=["POST"])
def login_endpoint():
    context = GlobalContext.get_instance()
    data = request.json
    login = data.get("login")
    password = data.get("password")
    valid_password = False

    db_handler = MongoDBHandler.from_default(context)
    user_object = db_handler.load_one("user", {"login": login})
    if user_object:
        valid_password = user_object.validate_password(password)
    else:
        print("no user object")

    if not valid_password:
        print("auth failed")
        return jsonify({"status": "KO"})

    return jsonify(
        {
            "status": "OK",
            "data": {
                "access_token": jwt.encode(
                    {"uid": user_object.oid}, "secret", algorithm="HS256"
                ),
            },
        }
    )
