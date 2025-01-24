import asyncio
import datetime
import threading
from typing import Dict, Optional, TYPE_CHECKING, Any, List, Mapping, cast

from conf import Config
from conf.config import RunMode
from core.callbacks.callback_handler import CallbackHandler
from core.callbacks.types import EventSenderParam
from core.tasks.types import Status

if TYPE_CHECKING:
    from core.context.context import Context


class ExecutionMemoryBuffer:
    def __init__(self, dag_id: str, status: Optional[Status] = None):
        self._dag_id = dag_id
        self._task_status: Dict[str, Status] = {}
        self._task_error: Dict[str, str] = {}
        self._status = status  # Status.IDLE
        self._error: Optional[Exception] = None
        self._progress: Optional[float] = None

        self._task_data: Dict[str, Dict[str, Any]] = {}
        self._task_stream: Dict[str, Dict[str, Any]] = {}

        self._has_content = False

    @property
    def has_content(self) -> bool:
        return self._has_content

    def clear(self):
        self._task_status.clear()
        self._task_error.clear()
        self._status = None
        self._error = None
        self._progress = None

        self._task_data.clear()
        self._task_stream.clear()
        self._has_content = False

    def set_task_status(self, sender, status, error: Optional[Exception] = None):
        self._task_status[sender] = status
        if error is not None:
            self._task_error[sender] = str(error)
        self._has_content = True

    def set_dag_status(self, status: Status, error: Optional[Exception] = None):
        self._status = status
        if error is not None:
            self._error = error
        self._has_content = True

    def set_progress(self, progress: float):
        self._progress = progress
        self._has_content = True

    def set_task_data(self, sender: str, key: str, value: Any):
        sender_dict = self._task_data.setdefault(sender, {})
        sender_dict[key] = value
        self._has_content = True

    def get_task_data_value(self, sender: str, key: str) -> Any:
        return self._task_data.get(sender, {}).get(key, None)

    def add_task_stream(self, sender: str, key: str, value: Any, reset: bool):
        sender_dict = self._task_stream.setdefault(sender, {})

        if reset:
            sender_dict.pop(key, None)

        if key in sender_dict:
            previous_val, reset = sender_dict[key]
        else:
            previous_val = [] if isinstance(value, list) else ""

        new_value = previous_val + value

        sender_dict[key] = (new_value, reset)
        self._has_content = True

    def as_payload(self) -> Mapping[str, Any]:
        ws_data: Dict[str, Any] = {}

        if self._task_status:
            ws_data["taskStatus"] = {
                sender_event_id: status.name
                for sender_event_id, status in self._task_status.items()
            }
            ws_data["taskError"] = {
                sender_event_id: error
                for sender_event_id, error in self._task_error.items()
            }

        if self._status:
            ws_data["dagStatus"] = {self._dag_id: self._status.name}
            ws_data["dagError"] = {
                self._dag_id: str(self._error) if self._error else ""
            }

        if self._progress:
            ws_data["dagProgress"] = {self._dag_id: self._progress}

        if self._task_data or self._task_stream:
            delta_values: List[Dict[str, Any]] = []

            for sender_event_id, data_map in self._task_data.items():
                for key, value in data_map.items():
                    delta_values.append(
                        {"task": sender_event_id, "id": key, "data": value}
                    )

            for sender_event_id, data_map in self._task_stream.items():
                for key, (value, reset) in data_map.items():
                    delta_values.append(
                        {
                            "task": sender_event_id,
                            "id": key,
                            "stream": value,
                            "reset": reset,
                        }
                    )

            ws_data["values"] = delta_values

            # send taskError empty

        return ws_data


class DagExecutionMemory(CallbackHandler):

    def __init__(self, dag_id: str):
        super().__init__()

        self._dag_id = dag_id
        self._acc_buffer = ExecutionMemoryBuffer(dag_id, Status.IDLE)
        self._tmp_buffer = ExecutionMemoryBuffer(dag_id)

        self._data_lock = asyncio.Lock()
        self._sent_lock = threading.Lock()
        self._is_scheduled = False

        conf = Config()

        self._subscription_count = 1 if conf.run_mode == RunMode.WORKER else 0

        self._ui_elements: List[Dict[str, Any]] = []

        self._start_date: Optional[datetime.datetime] = None
        self._end_date: Optional[datetime.datetime] = None

    def set_ui_elements(self, ui_elements: List[Dict[str, Any]]):
        self._ui_elements = ui_elements

    def serialize(self) -> Mapping[str, Any]:
        return {**super().serialize(), "dag_id": self._dag_id}

    @property
    def start_date(self) -> Optional[datetime.datetime]:
        return self._start_date

    @property
    def start_date_iso(self) -> Optional[str]:
        return self._start_date.isoformat() if self._start_date else None

    @property
    def end_date(self) -> Optional[datetime.datetime]:
        return self._end_date

    @property
    def end_date_iso(self) -> Optional[str]:
        return self._end_date.isoformat() if self._end_date else None

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> Any:
        from core.context.global_context import GlobalContext

        dag_id = data["dag_id"]
        return GlobalContext.get_instance().dag_manager.get_memory(dag_id)

    def is_event_handled(
        self, context: "Context", sender: EventSenderParam, event=False
    ) -> bool:
        from core.tasks.task import Task
        from core.tasks.task_dag import TaskDAG

        return (isinstance(sender, Task) and event in {"data", "status", "stream"}) or (
            isinstance(sender, TaskDAG)
            and event in {"status", "progress", "subscription", "unsubscription"}
        )

    async def on_handled_event(
        self,
        context: "Context",
        sender: EventSenderParam,
        event: str,
        payload: Optional[Mapping[str, Any]],
        raw_payload=False,
    ) -> bool:

        if not isinstance(payload, dict) or not event:
            return False

        from core.tasks.task import Task
        from core.tasks.task_dag import TaskDAG

        if isinstance(sender, Task):
            sender_event_id = sender.full_id

            if event == "status":
                status = cast(Status, payload.get("status"))
                error = cast(Optional[Exception], payload.get("error"))

                self._acc_buffer.set_task_status(sender_event_id, status, error)
                if self._subscription_count:
                    async with self._data_lock:
                        self._tmp_buffer.set_task_status(sender_event_id, status, error)

            elif event == "data":
                if self._subscription_count:
                    async with self._data_lock:
                        for key, value in payload.items():
                            prev_value = self._acc_buffer.get_task_data_value(
                                sender_event_id, key
                            )

                            if prev_value != value:
                                self._tmp_buffer.set_task_data(
                                    sender_event_id, key, value
                                )

                for key, value in payload.items():
                    self._acc_buffer.set_task_data(sender_event_id, key, value)

            elif event == "stream":
                for key, (value, reset) in payload.items():
                    self._acc_buffer.add_task_stream(sender_event_id, key, value, reset)

                if self._subscription_count:
                    async with self._data_lock:
                        for key, (value, reset) in payload.items():
                            self._tmp_buffer.add_task_stream(
                                sender_event_id, key, value, reset
                            )

        elif isinstance(sender, TaskDAG):
            if event == "subscription":
                self._subscription_count += 1

                await context.event(sender, "ws", self._acc_buffer.as_payload())

            elif event == "unsubscription":
                self._subscription_count -= 1

                if not self._subscription_count:
                    async with self._data_lock:
                        self._tmp_buffer.clear()

            elif event == "status":
                raw_status = payload.get("status")

                if not isinstance(raw_status, Status):
                    raise ValueError(
                        "status must be an instance of Status, {} given".format(
                            type(raw_status)
                        )
                    )

                self._acc_buffer.set_dag_status(raw_status, payload.get("error"))
                if self._subscription_count:
                    async with self._data_lock:
                        self._tmp_buffer.set_dag_status(
                            raw_status, payload.get("error")
                        )

                if raw_status == Status.RUNNING:
                    self._start_date = datetime.datetime.now()
                elif raw_status in {Status.FINISHED, Status.ERROR}:
                    self._end_date = datetime.datetime.now()

            elif event == "progress":
                progress_value = cast(float, payload["progress"])
                new_progress = round(progress_value, 3)

                self._acc_buffer.set_progress(new_progress)
                if self._subscription_count:
                    async with self._data_lock:
                        self._tmp_buffer.set_progress(new_progress)

        async with self._data_lock:
            should_send = self._tmp_buffer.has_content

        if should_send:
            with self._sent_lock:
                if not self._is_scheduled:
                    self._is_scheduled = True

                    async def schedule_function():
                        await asyncio.sleep(0.3)

                        async with self._data_lock:
                            ws_data = self._tmp_buffer.as_payload()
                            self._tmp_buffer.clear()

                            with self._sent_lock:
                                self._is_scheduled = False

                        await context.event(sender, "ws_dag_room", ws_data)

                    from core.context.global_context import GlobalContext

                    GlobalContext.run_task(schedule_function())

        return False

    def task_data(self, task_id: str, key: str) -> Any:
        return self._acc_buffer.get_task_data_value(task_id, key)
