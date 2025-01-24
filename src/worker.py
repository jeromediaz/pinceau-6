import asyncio
import json
import os

import socketio
from celery.exceptions import Ignore

from celery_factory import celery_factory
from conf import Config
from core.context.global_context import GlobalContext
from core.tasks.task_dag import TaskDAG
from core.tasks.types import JSONParam
from core.utils import deserialize_instance, load_local_application

os.environ["P6_RUN_MODE"] = "worker"

app = celery_factory()

global_context = GlobalContext()

config = Config()

# load_dag_folder("dag", "dag")
load_local_application("arxiv")
load_local_application("chat")
load_local_application("huggingface")
load_local_application("llama_index")
load_local_application("mangafox")
load_local_application("pinceau6")
# load_dag_folder("application/arxiv", "application.arxiv")

socket_client = config.get("SOCKET_CLIENT")

print("======================")
print(f"Socket client is {socket_client}")

sio = socketio.SimpleClient()
sio.connect(socket_client)
global_context.set_websocket_client(sio)
print(f"global-context {hex(id(global_context))}")


@app.task(bind=True)
def run_task(
    self, task_data: JSONParam, task_context: JSONParam, task_input: JSONParam
):
    if self.request.delivery_info["redelivered"]:
        raise Ignore()  # ignore if this task was redelivered
    print("This should only execute on first receipt of task")
    print(json.dumps(task_context))

    print(json.dumps(task_data))

    with TaskDAG():
        task_instance = deserialize_instance(task_data)
        work_context = deserialize_instance(task_context)

        result = asyncio.run(
            task_instance.process(work_context, task_input), debug=True
        )

        return result


print(app.tasks)
