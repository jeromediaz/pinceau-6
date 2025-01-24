from typing import TYPE_CHECKING, Mapping, Any, Optional, Dict, List, Tuple

from pydantic import BaseModel

from api.websocket_decorator import register_websocket_event
from core.tasks.types import JSONParam, Status

if TYPE_CHECKING:
    from core.context.global_context import GlobalContext
    from core.context.context import Context
    from core.tasks.task import Task
    from flask_socketio import SocketIO


class RelayData:
    sender: str
    payload: Mapping[str, Any] = {}


class RelayPayload(BaseModel):

    relay: dict
    to: str
    event: Optional[str] = None


@register_websocket_event()
async def worker_relay(
    payload: JSONParam, websocket: "SocketIO", context: "GlobalContext", **kwargs
):
    relay_payload = RelayPayload.model_validate(payload)
    data = relay_payload.relay
    data_payload = data.get("payload", {})

    from core.context.composite_context import CompositeContext
    from core.callbacks.websocket_callback_handler import WebsocketCallbackHandler
    from core.callbacks.dag_ws_callback_handler import DagWebsocketCallbackHandler

    work_context: Optional[CompositeContext]

    if relay_payload.event == "chatResponse":
        work_context = CompositeContext(context)
        if context.websocket_manager:
            chat_id = data_payload.get("chatId", "")
            chat_ws_callback = WebsocketCallbackHandler(
                context.websocket_manager.websocket, to=f"chat_{chat_id}"
            )

            work_context.create_local_context(callbacks=[chat_ws_callback])

            # FIXME: run inside event loop
            await work_context.event(
                "chat::" + chat_id,
                "chatResponse",
                data_payload,
                raw_payload=True,
            )
            return

    dag_context_map: Dict[str, CompositeContext] = {}

    def get_dag_context(dag_id: str) -> Optional[CompositeContext]:
        if dag_id in dag_context_map:
            return dag_context_map[dag_id]

        composite_context = CompositeContext(context)
        if context.websocket_manager:

            dag_callback = context.dag_manager.get_memory(dag_id)
            ws_callback = DagWebsocketCallbackHandler(
                context.websocket_manager.websocket, to=f"dag_{dag_id}"
            )

            composite_context.create_local_context(
                callbacks=[dag_callback, ws_callback]
            )
        dag_context_map[dag_id] = composite_context

        return composite_context

    for key, value in data_payload.get("taskStatus", {}).items():
        dag_id, task_id = key.split("::")
        status = getattr(Status, value)

        work_context = get_dag_context(dag_id)

        if not work_context:
            continue

        task_dag = work_context.dag_manager.get(dag_id)
        task_object = task_dag.task_node_map.get(task_id)
        if not task_object:
            continue
        await task_object.task.set_status(work_context, status)

    for dag_id, value in data_payload.get("dagStatus", {}).items():
        work_context = get_dag_context(dag_id)

        if not work_context:
            continue

        status = getattr(Status, value)
        task_dag = work_context.dag_manager.get(dag_id)
        await task_dag.set_status(work_context, status)

    for dag_id, value in data_payload.get("dagProgress", {}).items():
        work_context = get_dag_context(dag_id)

        if not work_context:
            continue

        task_dag = work_context.dag_manager.get(dag_id)
        await task_dag.set_progress(work_context, value)

    if "values" in data_payload:

        task_data: Dict[str, Dict[str, Any]] = {}
        task_stream: Dict[str, Dict[str, Any]] = {}
        task_map: Dict[str, Tuple["Task", "Context"]] = {}

        for value in data_payload["values"]:
            dag_id, task_id = value.pop("task").split("::")
            value_id = value.pop("id")
            work_context = get_dag_context(dag_id)

            if not work_context:
                continue

            task_dag = work_context.dag_manager.get(dag_id)
            task_object = task_dag.task_node_map.get(task_id)
            if not task_object:
                continue

            task_map[task_id] = (task_object.task, work_context)

            data = task_data.setdefault(task_id, {})
            stream = task_stream.setdefault(task_id, {})

            if "data" in value:
                data[value_id] = value["data"]
            if "stream" in value:
                stream[value_id] = (value["stream"], value.get("reset", False))

        for task_id, (task_object, task_work_context) in task_map.items():
            raw_data = task_data.get(task_id)

            if raw_data:
                await task_work_context.event(task_object, "data", raw_data)

            raw_stream = task_stream.get(task_id)
            if raw_stream:
                await task_work_context.event(task_object, "stream", raw_stream)

    if "uiElements" in data_payload:
        ui_elements_map: Dict[str, List[Any]] = {}

        for value in data_payload["uiElements"]:
            dag_id, task_id = value.get("task").split("::")

            ui_elements_list = ui_elements_map.setdefault(dag_id, list())
            ui_elements_list.append(value)

        for dag_id, elements in ui_elements_map.items():
            work_context = get_dag_context(dag_id)

            if not work_context:
                continue
            task_dag = work_context.dag_manager.get(dag_id)

            await work_context.event(task_dag, "", {"uiElements": elements})
