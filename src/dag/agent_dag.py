from core.tasks.task_dag import TaskDAG
from tasks.agent_log import AgentLog
from tasks.agent_task import AgentTask

with TaskDAG(id="agent") as dag:
    agent_task = AgentTask()
    log_task = AgentLog()

    agent_task >> log_task
