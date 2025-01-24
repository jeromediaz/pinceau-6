# This is a sample Python script.
import asyncio

from core.context.context import Context
from core.tasks.task_dag import TaskDAG
from tasks.agent_log import AgentLog
from tasks.agent_task import AgentTask


# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f"Hi, {name}")  # Press ⌘F8 to toggle the breakpoint.


async def historian_main():
    context = Context()

    events = [
        "google’s format docstring documentation for a method with parameters and raising an exception",
        # "positional and keyword arguments",
        # "abstract class definition",
        # "inheritance",
    ]
    agent_keys = ["python_instructor"]

    for _ in range(1):
        for event in events:
            for agent_key in agent_keys:
                with TaskDAG() as dag:
                    agent_task = AgentTask()
                    log_task = AgentLog()

                    agent_task >> log_task
                    # dag.add_task_child(agent_task, log_task)

                input = {
                    "event": event,
                    "agent": agent_key,
                }

                await context.run_dag(dag, input)


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    print_hi("PyCharm")
    asyncio.run(historian_main())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
