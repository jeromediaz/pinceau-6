from typing import TYPE_CHECKING

from core.utils import deserialize_instance

if TYPE_CHECKING:
    from apscheduler.schedulers.base import BaseScheduler
    from models.dag_persisted_model import DAGPersistedModel


def run_dag(dag_persisted_model: "DAGPersistedModel"):
    from core.context.global_context import GlobalContext

    global_context = GlobalContext.get_instance()

    context = deserialize_instance(dag_persisted_model.context)
    dag = global_context.dag_manager.get(dag_persisted_model.dag_id)

    if dag is None:
        raise RuntimeError(f"DAG not found {dag_persisted_model.dag_id}")

    data_input = dag_persisted_model.inputs

    GlobalContext.run_task(global_context.run_dag(dag, data_input, context))


class SchedulerManager(object):
    def __init__(self, scheduler: "BaseScheduler"):
        self._scheduler = scheduler

    def schedule_dag(self, dag_persisted: "DAGPersistedModel"):
        current_job = self._scheduler.get_job(dag_persisted.dag_id)

        if current_job is None and dag_persisted.scheduler is not None:
            trigger = dag_persisted.scheduler.as_trigger()

            self._scheduler.add_job(
                run_dag, trigger, [dag_persisted], id=dag_persisted.dag_id
            )

        elif current_job:
            self._scheduler.remove_job(dag_persisted.dag_id)

            if dag_persisted.scheduler is not None:
                trigger = dag_persisted.scheduler.as_trigger()

                self._scheduler.add_job(
                    run_dag, trigger, [dag_persisted], id=dag_persisted.dag_id
                )

    def unschedule_dag(self, dag_persisted: "DAGPersistedModel"):
        current_job = self._scheduler.get_job(dag_persisted.dag_id)

        if current_job:
            self._scheduler.remove_job(dag_persisted.dag_id)
