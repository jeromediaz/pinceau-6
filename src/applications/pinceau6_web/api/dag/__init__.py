from typing import TYPE_CHECKING, List, Mapping, Any, cast, Dict

from flask import jsonify, request, Response

from api.blueprint_decorator import register_route
from api.helpers import get_filters, get_range, get_sort
from api.security_wrapper import authentication
from applications.chat.models.chat_from_wrapped_dag import ChatFromWrappedDag
from conf import Config
from core.callbacks.dag_ws_callback_handler import DagWebsocketCallbackHandler
from core.context.global_context import GlobalContext
from core.context.user_context import UserContext
from core.database.mongodb import MongoDBHandler
from core.tasks.dag_calling_task import DAGCallingTask
from core.tasks.remote_task_wrapper import RemoteTaskWrapper
from core.tasks.task_dag import TaskDAG
from misc.functions import extract_dag_id, check_if_dag_chat_compatible
from ui.helper import ui_fields_from_base_model

if TYPE_CHECKING:
    from core.context.composite_context import CompositeContext
    from core.tasks.task_node import TaskEdge


@register_route("")
@authentication()
def graphs(context: "CompositeContext") -> Response:
    filters = get_filters()
    orders = get_sort()

    global_context = context.cast_as(GlobalContext)

    items = [
        dag_object.as_json()
        for dag_object in global_context.dag_manager.values(filters, orders)
    ]

    start, end = get_range()

    partial_items = items[start:end]

    end = start + len(items) - 1

    response = jsonify(partial_items)
    response.headers.add("Content-Range", f"graphs {start}-{end}/{len(items)}")

    return response


@register_route("/<string:dag_id>")
@authentication()
def dag(dag_id: str, context: "CompositeContext") -> Response:
    dag_identifier, dag_variant, _ = extract_dag_id(dag_id)

    if dag_id not in context.dag_manager and dag_identifier in context.dag_manager:
        parent_dag_object = context.dag_manager[dag_identifier]

        parent_dag_object.clone(dag_id)

    global_context = context.cast_as(GlobalContext)

    dag_object = global_context.dag_manager[dag_id]
    item: Dict[str, Any] = dag_object.as_json()

    params = []

    dag_params = dag_object.merge_params_input_models()
    if dag_params:
        dag_fields = ui_fields_from_base_model(dag_params)
        if dag_fields:
            params += [
                {
                    "type": "group",
                    "source": "__dag__",
                    "fields": dag_fields,
                }
            ]

    params += [
        {
            "type": "group",
            "source": task_id,
            "fields": ui_fields_from_base_model(model),
        }
        for task_id, model in dag_object.required_params().items()
    ]

    item["params"] = params

    global_context = context.cast_as(GlobalContext)
    variants = global_context.dag_manager.get_dag_variants(dag_identifier)
    dag_params = global_context.dag_manager.get_dag_task_parameters(
        dag_identifier, dag_variant
    )

    item["variants"] = variants
    item["dagParams"] = dag_params

    chat_compatible_data = check_if_dag_chat_compatible(dag_object)
    item["chatCompatible"] = (
        False
        if chat_compatible_data is None
        else {
            "input": [chat_compatible_data.input_key, chat_compatible_data.input_type],
            "output": [
                chat_compatible_data.output_key,
                chat_compatible_data.output_type,
            ],
        }
    )

    response = jsonify(item)

    return response


@register_route("/<string:dag_id>/chats", methods=["POST"])
@authentication()
def register_chats(dag_id: str, context: "CompositeContext") -> Response:
    payload = cast(Mapping[str, Any], request.json)

    user_context = context.cast_as(UserContext)
    user_id = user_context.user_id

    wrapping_object = ChatFromWrappedDag.from_default(
        user_id,
        dag_id,
        subject=cast(str, payload.get("chat_name")),
        input_type=payload.get("input_type"),
        input_field=payload.get("input_field"),
        output_type=payload.get("output_type"),
        output_field=payload.get("output_field"),
        job_payload={},
    )

    MongoDBHandler.from_default(context).save_object(context, wrapping_object, "chat")

    return_value = {"id": wrapping_object.id}

    return jsonify(return_value)


@register_route("/<string:dag_id>/graph")
@authentication()
def graph(dag_id: str, context: "CompositeContext") -> Response:

    item = context.dag_manager[dag_id]

    edges: List["TaskEdge"] = []
    for node in item.task_node_map.values():
        edges.extend(node.sub_nodes)

    nodes = {
        node.task.id: {"label": node.task.label} for node in item.task_node_map.values()
    }

    response = {"nodes": nodes, "edges": [edge.as_json() for edge in edges]}

    return jsonify(response)


@register_route("/<string:dag_id>/run", methods=["GET"])
@authentication()
def dag_contract(dag_id: str, context: "CompositeContext") -> Response:
    dag_object = context.dag_manager[dag_id]

    items = []

    if not dag_object.required_worker_tag:
        global_context = context.cast_as(GlobalContext)

        required_worker_tag_field = {
            "source": "__required_worker_tag__",
            "label": "Worker",
            "type": "select",
            "choices": [
                {"id": queue, "name": queue} for queue in global_context.celery_workers
            ],
            "optional": True,
        }
        items.append(required_worker_tag_field)

    for key, value in dag_object.get_required_inputs().fields_map().items():
        items.append({"source": key, **value})

    return jsonify(items)


@register_route("/<string:dag_id>/parameters", methods=["PUT"])
@authentication()
def register_params(dag_id: str, context: "CompositeContext") -> Response:

    dag_identifier, dag_variant, _ = extract_dag_id(dag_id)

    payload = cast(Mapping[str, Any], request.json)

    global_context = context.cast_as(GlobalContext)
    global_context.dag_manager.set_dag_task_parameters(
        dag_identifier, dag_variant, payload
    )

    return jsonify({"status": "OK"})


@register_route("/<string:dag_id>/parameters", methods=["DELETE"])
@authentication()
def delete_params(dag_id: str, context: "CompositeContext") -> Response:

    dag_identifier, dag_variant, _ = extract_dag_id(dag_id)

    global_context = context.cast_as(GlobalContext)
    global_context.dag_manager.remove_dag_task_parameters(dag_identifier, dag_variant)

    return jsonify({"status": "OK"})


@register_route("/<string:dag_id>/run", methods=["POST"])
@authentication()
def run_dag(dag_id: str, context: "CompositeContext") -> Response:
    dag_instance = context.dag_manager[dag_id]

    used_dag = dag_instance.clone()
    payload = request.json

    direct_mode = True

    required_worker_tag = used_dag.required_worker_tag or payload.pop(
        "__required_worker_tag__", ""
    )

    if required_worker_tag:
        config = Config()
        queues = config.get("WORKER_TAGS", default="celery").split(";")
        direct_mode = required_worker_tag in queues

    if not isinstance(payload, dict):
        return jsonify("KO")

    global_context = context.cast_as(GlobalContext)
    user_context = context.cast_as(UserContext)
    from core.context.composite_context import CompositeContext

    work_context = CompositeContext(global_context)

    if direct_mode:
        if global_context.websocket_manager:
            web_socket_callback = DagWebsocketCallbackHandler(
                global_context.websocket_manager.websocket,
                to=f"dag_{used_dag.original_id}",
            )

            dag_execution_callback = global_context.dag_manager.get_memory(
                used_dag.original_id
            )

            work_context.create_local_context(
                callbacks=[dag_execution_callback, web_socket_callback]
            )

        work_context.add_layer(user_context)

        GlobalContext.run_task(context.run_dag(used_dag, payload, work_context))
    else:
        with TaskDAG(
            id=f"{used_dag.id}-remote",
            original_id=used_dag.id,
            tags=[*used_dag.tags, "remote"],
            parent_id=used_dag.id,
        ) as remote_dag:
            RemoteTaskWrapper(
                DAGCallingTask(used_dag.id, id="dag_calling", _register_task=False),
                worker_tag=required_worker_tag,
                id="remote_call",
            )

        if global_context.websocket_manager:
            web_socket_callback = DagWebsocketCallbackHandler(
                global_context.websocket_manager.websocket,
                to=f"dag_{remote_dag.original_id}",
            )

            dag_execution_callback = global_context.dag_manager.get_memory(
                remote_dag.original_id
            )

            work_context.create_local_context(
                callbacks=[dag_execution_callback, web_socket_callback]
            )

        work_context.add_layer(user_context)

        print(f"context run task remote {remote_dag} {payload=}")
        GlobalContext.run_task(context.run_dag(remote_dag, payload, work_context))

    return_value = {"dagId": used_dag.id, "parentId": used_dag.parent_id}

    return jsonify(return_value)


@register_route("/<string:dag_id>/persist", methods=["POST"])
@authentication()
def persist_dag(dag_id: str, context: "CompositeContext") -> Response:
    dag_object = context.dag_manager[dag_id]

    used_dag = dag_object.clone()

    payload = request.json

    if not isinstance(payload, dict):
        return jsonify("KO")

    from models.dag_persisted_model import DAGPersistedModel

    global_context = context.cast_as(GlobalContext)
    user_context = context.cast_as(UserContext)
    from core.context.composite_context import CompositeContext

    work_context = CompositeContext(global_context)

    if global_context.websocket_manager:
        web_socket_callback = DagWebsocketCallbackHandler(
            global_context.websocket_manager.websocket, to=f"dag_{used_dag.id}"
        )

        dag_execution_callback = global_context.dag_manager.get_memory(used_dag.id)

        work_context.create_local_context(
            callbacks=[dag_execution_callback, web_socket_callback]
        )

    work_context.add_layer(user_context)

    persisted_dag = DAGPersistedModel(
        parent_dag_id=dag_id,
        dag_id=used_dag.id,
        label=dag_id,
        inputs=payload,
        context=work_context.serialize(),
        trigger=None,
    )

    MongoDBHandler.from_default(context).save_object(context, persisted_dag)

    return_value = {"id": persisted_dag.id}

    return jsonify(return_value)


@register_route("/<string:dag_id>.svg", methods=["GET"])
@authentication(check_authorization=False)
def svg(dag_id: str, context: "CompositeContext") -> Response:
    dag_object = context.dag_manager[dag_id]

    return Response(dag_object.as_graph().create_svg(), mimetype="image/svg+xml")


@register_route("/<string:dag_id>.png", methods=["GET"])
@authentication()
def png(dag_id: str, context: "CompositeContext") -> Response:
    dag_object = context.dag_manager[dag_id]

    return Response(dag_object.as_graph().create_png(), mimetype="image/png")


@register_route("/<string:dag_id>/tasks", methods=["GET"])
@authentication()
def tasks(dag_id: str, context: "CompositeContext") -> Response:
    dag_object = context.dag_manager[dag_id]

    task_list = dag_object.tasks_list()
    response = jsonify(task_list)
    response.headers.add("Content-Range", f"graphs 0-{len(task_list)}/{len(task_list)}")

    return response
