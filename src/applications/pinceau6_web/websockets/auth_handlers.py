from typing import TYPE_CHECKING

import flask
import jwt
from flask import copy_current_request_context
from flask_socketio import disconnect

from api.websocket_decorator import register_websocket_event
from core.database.mongodb import MongoDBHandler

if TYPE_CHECKING:
    from core.context.global_context import GlobalContext
    from flask_socketio import SocketIO
    from core.managers.websocket_auth_manager import WebsocketAuthManager


@register_websocket_event()
async def connect(
    websocket: "SocketIO",
    context: "GlobalContext",
    websocket_auth_manager: "WebsocketAuthManager",
):
    session_id = flask.request.sid  # type: ignore
    print(f"connect_handler {session_id=}")
    if websocket_auth_manager.is_registered():
        return

    @copy_current_request_context
    def disconnect_if_not_authenticated():
        if not websocket_auth_manager.is_registered(sid=session_id):
            disconnect(sid=session_id)

    def ack(token: str = ""):
        if not token:
            disconnect(sid=session_id)
            return False

        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        uid = payload.get("uid")

        db_handler = MongoDBHandler.from_default(context)
        user_object = db_handler.load_one("user", {"_id": uid})
        websocket_auth_manager.set_user_data(user_object)

    try:
        pass
    except AssertionError:
        pass


@register_websocket_event("disconnect")
async def disconnect_handler(websocket_auth_manager: "WebsocketAuthManager", **kwargs):
    session_id = flask.request.sid  # type: ignore
    print(f"disconnect_handler {session_id=}")

    websocket_auth_manager.remove_user_data()
