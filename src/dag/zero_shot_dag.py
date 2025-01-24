from core.tasks.task_dag import TaskDAG
from tasks.wait_task import WaitTask
from tasks.zero_shot_branching_task import ZeroShotBranchingTask
from tasks.zero_shot_classification_task import ZeroShotClassificationTask


with TaskDAG(id="zero_shot"):
    ZeroShotClassificationTask()

with TaskDAG(id="zero_shot_branching"):
    branching_task = ZeroShotBranchingTask(id="branching")

    wait_one = WaitTask(5, id="one", label="+ananas", description="include ananas")
    wait_two = WaitTask(5, id="two", label="-ananas", description="exclude ananas")
    wait_three = WaitTask(
        5, id="three", label="other", description="ananas not mentioned"
    )

    branching_task >> wait_one
    branching_task >> wait_two
    branching_task >> wait_three
