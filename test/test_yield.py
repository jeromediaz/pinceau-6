import asyncio
import os
import pathlib

from core.callbacks.dag_execution_memory import DagExecutionMemory
from core.callbacks.dag_execution_tracer import DAGExecutionTracer
from core.callbacks.tasks_execution_tracer import TasksExecutionTracer
from core.context.composite_context import CompositeContext
from core.context.global_context import GlobalContext
from core.tasks.types import Status
from core.utils import load_dag_folder


def test_test_yield():
    os.environ["P6_LOAD_PERSIST_MODELS"] = "False"
    os.environ["P6_RUN_MODE"] = "TEST"

    os.chdir(os.path.join(pathlib.Path(__file__).parent, "../src"))
    global_context = GlobalContext.get_instance()

    load_dag_folder("dag", "dag")

    dag = global_context.dag_manager.get("test_yield")

    assert dag is not None

    test_context = CompositeContext(global_context)

    dag_tracer = DAGExecutionTracer("test_yield")
    dag_memory = DagExecutionMemory("test_yield")
    tasks_tracer = TasksExecutionTracer("test_yield")

    test_context.create_local_context(callbacks=[tasks_tracer, dag_memory, dag_tracer])

    asyncio.run(global_context.run_dag(dag, {}, test_context))

    assert dag_tracer.last_status == Status.FINISHED

    assert tasks_tracer.known_tasks == 9

    assert (
        len(
            tasks_tracer.task_status_start_duration("test_yield::range", Status.RUNNING)
        )
        == 1
    )

    tasks_tracer.task_start_duration("test_yield::A")
    assert (
        len(tasks_tracer.task_status_start_duration("test_yield::A", Status.RUNNING))
        == 5
    )

    assert (
        len(
            tasks_tracer.task_status_start_duration(
                "test_yield::round_robin", Status.RUNNING
            )
        )
        == 5
    )

    assert (
        len(tasks_tracer.task_status_start_duration("test_yield::B", Status.RUNNING))
        == 3
    )

    assert (
        len(tasks_tracer.task_status_start_duration("test_yield::D", Status.RUNNING))
        == 3
    )

    assert (
        len(tasks_tracer.task_status_start_duration("test_yield::C", Status.RUNNING))
        == 2
    )

    assert (
        len(tasks_tracer.task_status_start_duration("test_yield::E", Status.RUNNING))
        == 2
    )

    assert (
        len(
            tasks_tracer.task_status_start_duration(
                "test_yield::BEFORE", Status.RUNNING
            )
        )
        == 1
    )

    assert (
        len(
            tasks_tracer.task_status_start_duration("test_yield::AFTER", Status.RUNNING)
        )
        == 1
    )

