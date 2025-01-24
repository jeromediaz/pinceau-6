import asyncio
import logging
import threading
from typing import Optional, Any, TYPE_CHECKING, Mapping, List

import cachetools.func

from conf.config import Config, RunMode
from core.callbacks.dag_execution_counter import DAGExecutionCounter
from core.callbacks.dag_ws_callback_handler import DagWebsocketCallbackHandler
from core.context.composite_context import CompositeContext
from core.context.context import Context
from core.managers.applications_manager import ApplicationsManager
from core.managers.dbms_manager import DBMSManager
from core.managers.model_manager import ModelsManager
from core.managers.object_lock_manager import ObjectLockManager
from core.managers.scheduler_manager import SchedulerManager
from core.managers.websocket_manager import WebsocketManager
from core.tasks.types import Status, TaskData

if TYPE_CHECKING:
    from core.tasks.task_dag import TaskDAG
    from core.managers.dag_manager import DagManager
    from socket import SocketIO
    from apscheduler.schedulers.base import BaseScheduler

logger = logging.getLogger(__name__)


class GlobalContext(Context):
    INSTANCE: Optional["GlobalContext"] = None

    def __init__(self) -> None:
        self._config = Config()

        callbacks = (
            [DAGExecutionCounter()] if self._config.run_mode == RunMode.API else []
        )
        super().__init__(callbacks=callbacks)
        GlobalContext.INSTANCE = self

        self.memory: dict = dict()

        from core.managers.dag_manager import DagManager

        self.dbms = DBMSManager()

        self._dag_manager = DagManager(self)

        self.loop = asyncio.get_event_loop()
        self.websocket_manager: Optional[WebsocketManager] = None
        self._websocket_client: Optional[Any] = None
        self._scheduler_manager: Optional[SchedulerManager] = None
        self._applications_manager = ApplicationsManager(self)

        self.models_manager: ModelsManager = ModelsManager()
        self._object_lock_manager = ObjectLockManager()

        self.celery = None
        self._flask_app = None

    def serialize(self) -> Mapping[str, Any]:
        serialize = {
            **super().serialize(),
        }
        serialize.pop("_callback_manager", None)
        return serialize

    def set_flask_app(self, flask_app: Any) -> None:
        self._flask_app = flask_app

    @property
    def flask_app(self) -> Any:
        return self._flask_app

    @property
    def dag_manager(self) -> "DagManager":
        return self._dag_manager

    @property
    def object_lock_manager(self) -> "ObjectLockManager":
        return self._object_lock_manager

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> Any:
        if hasattr(cls, "INSTANCE"):
            instance_value = getattr(cls, "INSTANCE")
            if instance_value:
                return instance_value

        return cls()

    @property
    def config(self) -> Config:
        return self._config

    def set_websocket(self, socket: "SocketIO"):
        self.websocket_manager = WebsocketManager(socket, self)
        self.websocket_manager.register_handlers()

    @property
    def websocket_client(self):
        return self._websocket_client

    @property
    def applications_manager(self) -> ApplicationsManager:
        return self._applications_manager

    def set_websocket_client(self, client) -> None:
        self._websocket_client = client

    @property
    def scheduler_manager(self) -> Optional[SchedulerManager]:
        return self._scheduler_manager

    def set_scheduler(self, scheduler: "BaseScheduler") -> None:
        self._scheduler_manager = SchedulerManager(scheduler)

        logger.info(
            "scheduler given",
        )

        if self._dag_manager:
            for scheduled_dag in self._dag_manager.scheduled_persisted_dag_models():
                logger.info(f"scheduling {scheduled_dag}")
                self._scheduler_manager.schedule_dag(scheduled_dag)

    def set_celery_client(self, celery) -> None:
        self.celery = celery

    @property
    @cachetools.func.ttl_cache(ttl=10 * 60)
    def celery_workers(self) -> List[str]:
        if not self.celery:
            return []

        tags = set()
        active_queues = self.celery.control.inspect().active_queues()
        if active_queues:
            for host, info_list in active_queues.items():
                for info in info_list:
                    tags.add(info.get("name"))

        return list(tags)

    def get_dbms(self, key: str) -> Any:
        return self.dbms[key]

    @classmethod
    def get_instance(cls) -> "GlobalContext":
        if not GlobalContext.INSTANCE:
            return GlobalContext()

        return GlobalContext.INSTANCE

    def register_dag(self, dag: "TaskDAG") -> None:
        logger.info("DAG %s registered", dag.id)
        self.dag_manager[dag.id] = dag

    async def run_dag(
        self, dag: "TaskDAG", data_input: TaskData, context: Optional["Context"] = None
    ) -> None:

        work_context = None
        try:

            if context is not None:
                work_context = context
            else:
                work_context = CompositeContext(self)
                if self.websocket_manager:
                    web_socket_callback = DagWebsocketCallbackHandler(
                        self.websocket_manager.websocket, to=f"dag_{dag.original_id}"
                    )

                    dag_execution_callback = self._dag_manager.get_memory(
                        dag.original_id
                    )

                    work_context.create_local_context(
                        callbacks=[dag_execution_callback, web_socket_callback]
                    )
        except Exception as e:
            logger.exception("run_dag get work_context")
            if work_context:
                await dag.set_status(work_context, Status.ERROR, error=e)

        if not work_context:
            return

        try:
            await dag.set_status(work_context, Status.RUNNING, send_value=False)
            await dag.reset_task_status(work_context)

            async with asyncio.TaskGroup() as tg:
                dag.set_task_group(tg)
                root_tasks = dag.get_root_tasks()

                for task in root_tasks:
                    tg.create_task(dag.schedule_task(work_context, task, data_input))

            dag.set_task_group(None)

            await dag.dag_did_finish()
            await dag.set_status(work_context, Status.FINISHED)
        except Exception as e:
            logger.exception("run_dag")
            print(e)
            await dag.set_status(work_context, Status.ERROR, error=e)

    @staticmethod
    def run_task(coroutine) -> None:
        try:
            thread = threading.Thread(target=asyncio.run, args=(coroutine,))

            thread.start()

        except Exception as e:
            print(e)
            logger.exception("run_task")
