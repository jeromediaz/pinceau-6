from functools import wraps

import jwt
from flask import request, abort

from conf import Config
from core.context.composite_context import CompositeContext
from core.context.global_context import GlobalContext
from core.context.user_context import UserContext
from misc.functions import strtobool

config = Config()
check_authorization_default = not strtobool(
    config.get("DISABLE_API_SECURITY", default="False")
)


def authentication(check_authorization=check_authorization_default):

    def wrapper(fn):

        @wraps(fn)
        def decorated_endpoint_handler(*args, **kwargs):
            global_context = GlobalContext.get_instance()

            if not check_authorization:
                context = CompositeContext(global_context)
                return fn(*args, context=context, **kwargs)

            authorization = request.headers.get("Authorization", "")
            token = (
                authorization[6:].strip()
                if authorization.lower().startswith("bearer")
                else ""
            )

            if not token:
                abort(401)

            payload = jwt.decode(token, "secret", algorithms=["HS256"])
            uid = payload.get("uid")

            user_context = UserContext(uid)

            context = CompositeContext(global_context, user_context)

            return fn(*args, context=context, **kwargs)

        return decorated_endpoint_handler

    return wrapper
