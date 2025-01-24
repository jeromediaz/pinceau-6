from core.tasks.task_dag import TaskDAG
from tasks.extract_keywords_keybert_task import ExtractKeywordsBertTask
from tasks.extract_keywords_task import ExtractKeywordsTask

with TaskDAG(id="keywords_bert", required_worker_tag="MM1"):
    ExtractKeywordsBertTask(id="bert", label="BERT")


with TaskDAG(id="keywords"):
    ExtractKeywordsTask()
