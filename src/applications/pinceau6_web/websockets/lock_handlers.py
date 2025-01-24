from typing import TYPE_CHECKING

import flask
from flask_socketio import join_room
from pydantic import BaseModel, Field

from api.websocket_decorator import register_websocket_event
from core.tasks.types import JSONParam

if TYPE_CHECKING:
    from core.context.global_context import GlobalContext


class AcquireLockPayload(BaseModel):
    lock_id: str = Field(alias="lockId")


@register_websocket_event()
async def acquire_lock(
    payload: "JSONParam", websocket, context: "GlobalContext", **kwargs
):

    lock_payload = AcquireLockPayload.model_validate(payload)
    print(f"acquire_lock {lock_payload.lock_id=}")
    lock_manager = context.object_lock_manager

    session_id = flask.request.sid

    if lock_manager.try_acquire_lock(session_id, lock_payload.lock_id):
        return True

    join_room(f"lock_{lock_payload.lock_id}")
    return False


@register_websocket_event()
async def release_lock(
    payload: "JSONParam", websocket, context: "GlobalContext", **kwargs
):
    lock_payload = AcquireLockPayload.model_validate(payload)

    lock_manager = context.object_lock_manager

    session_id = flask.request.sid
    lock_manager.release_lock(websocket, session_id, lock_payload.lock_id)


@register_websocket_event("disconnect")
async def disconnect_handler(websocket, context: "GlobalContext", **kwargs):
    session_id = flask.request.sid  # type: ignore
    print(f"disconnect_handler {session_id=}")

    context.object_lock_manager.release_all_locks(websocket, session_id)
