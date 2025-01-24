import types
from functools import wraps
from typing import Optional, Callable, Union, cast

from werkzeug.exceptions import abort


def register_route(rule, endpoint: Optional[str] = None, **rule_kwargs):
    def my_decorator(func):
        final_endpoint = endpoint if endpoint else func.__name__
        print(rule)
        def wrapper(blueprint, **params):
            endpoint_enabled = cast(
                Union[Callable[[dict], bool], bool], rule_kwargs.pop("enabled", True)
            )
            if callable(endpoint_enabled):
                endpoint_enabled = endpoint_enabled(**params)

            if endpoint_enabled:
                blueprint.route(
                    rule, endpoint=final_endpoint, defaults=params, **rule_kwargs
                )(func)

        wrapper.is_url_rule = True
        return wrapper

    return my_decorator


def action_required(action: str, resource: str):
    def my_decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            from core.context.composite_context import CompositeContext
            from core.context.user_context import UserContext

            context = cast(CompositeContext, kwargs.get("context"))
            user_context = context.cast_as(UserContext)

            resource_parts = []
            for rsc_part in resource.split("/"):
                if rsc_part.startswith("<") and rsc_part.endswith(">"):
                    resource_parts.append(kwargs[rsc_part[1:-1]])
                else:
                    resource_parts.append(rsc_part)

            if not user_context.is_allowed(action, "/".join(resource_parts)):
                abort(404)

            return func(*args, **kwargs)

        return decorated_view

    return my_decorator


def is_register_route(func) -> bool:
    return isinstance(func, types.FunctionType) and getattr(func, "is_url_rule", False)
