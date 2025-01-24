from typing import TYPE_CHECKING

from applications.chat.tasks.chat_extract_keywords_task import ChatExtractKeywordsTask
from applications.chat.tasks.chat_task import ChatTask
from applications.chat.tasks.chat_user_branching_task import ChatUserBranchingTask
from applications.chat.tasks.chat_zero_shot_branching_task import (
    ChatZeroShotBranchingTask,
)
from applications.chat.tasks.index_arxiv_task import IndexArxivTask
from core.context.global_context import GlobalContext
from core.tasks.dag_calling_task import DAGCallingTask
from core.tasks.remote_task_wrapper import RemoteTaskWrapper
from core.tasks.task_dag import TaskDAG

if TYPE_CHECKING:
    from core.context.chat_context import ChatContext
    from core.context.composite_context import CompositeContext


async def chat_display_dag_handler(context: "CompositeContext", **kwargs):
    dag_id = "chat"  # todo: set it in the context

    global_context = GlobalContext.get_instance()
    dag_object = global_context.dag_manager[dag_id]

    png = dag_object.as_graph().create_png()
    import base64

    b64_part = base64.b64encode(png).decode("ASCII")

    data_uri = "data:image/png;base64," + b64_part

    await context.add_photo_message(context, data_uri, "agent:system")

    return {**kwargs}


async def chat_rag_handler(context: "CompositeContext", message: str, **kwargs):
    from core.context.session_context import SessionContext

    from core.context.chat_context import ChatContext

    chat_context = context.cast_as(ChatContext)

    session_context = SessionContext.get_context("1")
    chat_history = chat_context.extract_chat_history(
        context.get("from_user"), context.get("to_user")
    )

    chat_engine = session_context.get_chat_engine(
        chat_context.chat_id, chat_history=chat_history
    )
    response = chat_engine.chat(message)

    # asyncio.set_event_loop(local_event_loop)
    print("before chat context")
    await chat_context.add_text_message(
        context,
        response.response,
        context.get("to_user"),
        context.get("from_user"),
        "left",
    )

    print("before return")
    return {**kwargs}


async def chat_finished_handler(context: "CompositeContext", **kwargs):
    from core.context.chat_context import ChatContext

    chat_context = context.cast_as(ChatContext)
    await chat_context.add_system_message(context, "finished !", "agent:system")

    return {**kwargs}


with TaskDAG(id="chat") as dag:
    user_branching_task = ChatUserBranchingTask(
        id="router", default="rag", label="Agent router"
    )
    chat_system_task = ChatZeroShotBranchingTask(
        id="system", label="System agent intention router"
    )
    chat_extract_keywords_task = ChatExtractKeywordsTask(
        id="system_extract_keywords",
        description="I want you to learn about a subject",
        label="Keywords extractor",
    )
    chat_display_dag = ChatTask(
        id="display_dag",
        handler=chat_display_dag_handler,
        label="DAG",
        description="I want to see the DAG",
    )
    indexing_finished_task = ChatTask(
        id="indexing_finished", handler=chat_finished_handler, label="Finished message"
    )
    index_arxiv_task = IndexArxivTask(id="system_arxiv_index", label="Arxiv ingestion")
    chat_rag_task = ChatTask(id="rag", handler=chat_rag_handler, label="RAG agent")

    user_branching_task >> chat_system_task
    user_branching_task >> chat_rag_task
    (
        chat_system_task
        >> chat_extract_keywords_task
        >> index_arxiv_task
        >> indexing_finished_task
    )

    chat_system_task >> chat_display_dag


def refresh_chat_handler(context: "ChatContext", **kwargs):
    from applications.chat.websockets.chat_handlers import emit_chat_room_messages

    chat_id = context.chat_id
    emit_chat_room_messages(chat_id)

    return {**kwargs}


with TaskDAG(id="chat-remote") as dag:
    invoke = RemoteTaskWrapper(
        DAGCallingTask("chat", id="dag_calling", _register_task=False), id="remote_call"
    )
