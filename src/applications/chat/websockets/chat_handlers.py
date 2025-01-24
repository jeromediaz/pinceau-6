from typing import TYPE_CHECKING, cast

from flask_socketio import join_room, leave_room, emit
from pydantic import BaseModel

from api.websocket_decorator import register_websocket_event
from conf import Config
from core.callbacks.dag_ws_callback_handler import DagWebsocketCallbackHandler
from core.callbacks.websocket_callback_handler import WebsocketCallbackHandler
from core.context.composite_context import CompositeContext
from core.context.user_context import UserContext
from core.database.mongodb import MongoDBHandler
from core.tasks.remote_task_wrapper import RemoteTaskWrapper
from core.tasks.serialized_dag_processing_task import SerializedDAGProcessingTask
from core.tasks.task_dag import TaskDAG

if TYPE_CHECKING:
    from core.context.global_context import GlobalContext
    from flask_socketio import SocketIO
    from core.tasks.types import JSONParam


class ChatRoomPayload(BaseModel):
    chat_id: str

    @property
    def room_name(self) -> str:
        return f"chat_{self.chat_id}"


class ChatMessagePayload(ChatRoomPayload):
    user_id: str
    message: str
    uuid: str


def emit_chat_room_messages(chat_id: str) -> None:
    from core.context.chat_context import ChatContext

    chat_context = ChatContext.get_context(chat_id)

    chat_messages_array = list(
        map(
            lambda message: message.to_json_dict(),
            chat_context.message_list,
        )
    )

    emit(
        "chatResponse",
        {
            "chatId": chat_id,
            "messages": chat_messages_array,
        },
    )


@register_websocket_event()
async def enter_chat_room(payload: "JSONParam", context: "GlobalContext", **kwargs):
    chat_room_payload = ChatRoomPayload.model_validate(payload)

    join_room(chat_room_payload.room_name)

    from core.context.chat_context import ChatContext
    from applications.chat.tasks.chat_user_branching_task import ChatUserBranchingTask

    chat_context = ChatContext.get_context(chat_room_payload.chat_id)

    # TODO: save list of chats in mongo
    chat_dag = context.dag_manager["chat"]
    user_branching_task_gen = (
        task
        for task in chat_dag.get_root_tasks()
        if isinstance(task, ChatUserBranchingTask)
    )

    user_branching_task = next(user_branching_task_gen, None)
    agent_map = dict()
    if user_branching_task:
        user_branching_task_node = chat_dag.task_node_map[user_branching_task.id]

        agents = [sub_node.to_id for sub_node in user_branching_task_node.sub_nodes]

        mongo_db_handler = MongoDBHandler.from_default(context)

        agent_list = mongo_db_handler.load_multiples(
            "character", {"login": {"$in": agents}}
        )

        for agent in agent_list:
            json_value = agent.to_json_dict()
            agent_map[json_value["login"]] = json_value

    chat_messages_array = list(
        map(
            lambda message: message.to_json_dict(),
            chat_context.message_list,
        )
    )

    emit(
        "chatResponse",
        {
            "chatId": chat_room_payload.chat_id,
            "messages": chat_messages_array,
            "agents": agent_map,
        },
    )


@register_websocket_event()
async def leave_chat_room(payload: "JSONParam", **kwargs):
    chat_room_payload = ChatRoomPayload.model_validate(payload)
    leave_room(chat_room_payload.room_name)


@register_websocket_event("chatMessage")
async def chat_message(
    payload: "JSONParam", websocket: "SocketIO", context: "CompositeContext", **kwargs
):
    chat_message_payload = ChatMessagePayload.model_validate(payload)

    chat_id = chat_message_payload.chat_id
    user_id = chat_message_payload.user_id
    message = chat_message_payload.message

    from core.context.chat_context import ChatContext
    from applications.chat.models.a_chat_message import MessageStatus

    user_context = UserContext(user_id=user_id)

    chat_context = ChatContext.get_context(chat_id)

    dag_to_run = chat_context.chat.as_dag()

    dag_callback = context.dag_manager.get_memory(dag_to_run.original_id)

    # send only to subscriber

    dag_web_socket_callback = DagWebsocketCallbackHandler(
        context.websocket_manager.websocket, to=f"dag_{dag_to_run.original_id}"
    )
    chat_web_socket_callback = WebsocketCallbackHandler(websocket, to=f"chat_{chat_id}")

    callbacks = [dag_callback, dag_web_socket_callback, chat_web_socket_callback]

    run_chat_context = CompositeContext(context)
    # add socket layer
    run_chat_context.create_local_context(callbacks=callbacks)
    run_chat_context.add_layer(user_context)
    run_chat_context.add_layer(chat_context)

    input_message = await chat_context.add_text_message(
        run_chat_context,
        message,
        "user",
        "agent:default",
        "right",
        status=MessageStatus.RECEIVED,
        uuid=chat_message_payload.uuid,
    )

    await chat_context.update_message(run_chat_context, input_message)

    message_context = run_chat_context.create_local_context()

    message_context.set("from_user", "user")
    message_context.set("to_user", "agent:default")
    message_context.set("input_message", input_message)

    direct_mode = True
    worker_tag = dag_to_run.required_worker_tag
    if worker_tag:
        config = Config()
        queues = config.get("WORKER_TAGS", default="celery").split(";")
        direct_mode = worker_tag in queues

    if direct_mode:
        await context.run_dag(dag_to_run, payload, context=run_chat_context)
        return

    with TaskDAG(
        id=f"{dag_to_run.id}-remote",
        original_id=dag_to_run.id,
        tags=[*dag_to_run.tags, "remote"],
        parent_id=dag_to_run.id,
    ) as remote_dag:
        RemoteTaskWrapper(
            SerializedDAGProcessingTask(
                dag_to_run, id="dag_processing", _register_task=False
            ),
            worker_tag=cast(str, worker_tag),
            id="remote_call",
        )

        await context.run_dag(remote_dag, payload, context=run_chat_context)
