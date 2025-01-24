from applications.inproj.tasks.inproj_list_artefacts_task import ListArtefactsTask
from applications.inproj.tasks.inproj_list_lock_file_task import ListLockfileTask
from applications.inproj.tasks.inproj_list_projects_task import ListProjectsTask
from applications.inproj.tasks.inproj_process_lock_file_task import ProcessLockfileTask
from core.tasks.task_dag import TaskDAG

with TaskDAG(id="inproj_dag"):
    projects = ListProjectsTask(id="list_projects")
    artefacts = ListArtefactsTask(id="list_artefacts")
    lock_files = ListLockfileTask(id="list_lockfiles")
    process_lock_file = ProcessLockfileTask(id="process_lockfile")

    projects >> artefacts >> lock_files >> process_lock_file
