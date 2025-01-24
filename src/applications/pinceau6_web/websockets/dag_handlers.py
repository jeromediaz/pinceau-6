from typing import TYPE_CHECKING, List

import flask
from flask_socketio import join_room, leave_room
from pydantic import BaseModel

from api.websocket_decorator import register_websocket_event
from core.callbacks.dag_ws_callback_handler import DagWebsocketCallbackHandler
from core.context.composite_context import CompositeContext
from core.tasks.types import JSONParam

if TYPE_CHECKING:
    from core.context.global_context import GlobalContext
    from flask_socketio import SocketIO
    from core.callbacks.callback import Callback


class DAGPayload(BaseModel):

    dag: str

    @property
    def room_name(self) -> str:
        return f"dag_{self.dag}"


@register_websocket_event()
async def subscribe_dag(
    payload: JSONParam, websocket: "SocketIO", context: "GlobalContext", **kwargs
):
    dag_payload = DAGPayload.model_validate(payload)
    dag_id = dag_payload.dag
    dag = context.dag_manager.get(dag_id)

    if not dag:
        print("NOT DAG")
        return

    room_name = dag_payload.room_name
    join_room(room_name)

    work_context = CompositeContext(context)

    dag_callback = context.dag_manager.get_memory(dag_id)

    # send only to subscriber
    callbacks: List["Callback"] = [dag_callback]
    if context.websocket_manager:
        web_socket_callback = DagWebsocketCallbackHandler(
            context.websocket_manager.websocket, to=getattr(flask.request, "sid")
        )
        callbacks.append(web_socket_callback)

    work_context.create_local_context(callbacks=callbacks)

    await work_context.event(dag, "subscription", {})


@register_websocket_event()
async def unsubscribe_dag(payload: "JSONParam", context: "GlobalContext", **kwargs):
    dag_payload = DAGPayload.model_validate(payload)
    room_name = dag_payload.room_name
    leave_room(room_name)

    dag_id = dag_payload.dag
    dag = context.dag_manager.get(dag_id)

    if not dag:
        print("NOT DAG")
        return

    work_context = CompositeContext(context)

    dag_callback = context.dag_manager.get_memory(dag_id)

    work_context.create_local_context(callbacks=[dag_callback])

    await work_context.event(dag, "unsubscription", {})


@register_websocket_event()
async def subscribe_running_dag_count(
    payload: "JSONParam", context: "GlobalContext", **kwargs
):
    # TODO: read uid from payload
    join_room("runningDagRoom")

    await context.event("global", "subscribe_running_dag_count", {})


@register_websocket_event()
async def unsubscribe_running_dag_count(
    payload: "JSONParam", context: "GlobalContext", **kwargs
):
    del payload  # unused here
    del context  # unused here
    leave_room("runningDagRoom")
