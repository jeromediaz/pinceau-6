from core.tasks.task_dag import TaskDAG
from tasks.agent_character import AgentCharacter
from tasks.agent_story_next_step import AgentStoryNextStep


def story_dag():
    with TaskDAG(id="story") as dag:
        agent_character = AgentCharacter()

        agent_story_next_step = AgentStoryNextStep()

        agent_character >> agent_story_next_step
        dag.add_child_task(agent_character, agent_story_next_step)
