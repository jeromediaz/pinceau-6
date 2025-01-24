from core.tasks.task_dag import TaskDAG
from tasks.bostik_prompt_task import BostikPromptTask


with TaskDAG(id="bostik_prompt", tags=["eurelis"]) as dag:
    BostikPromptTask()
