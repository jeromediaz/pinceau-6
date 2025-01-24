from core.tasks.task_dag import TaskDAG
from tasks.ask_wikipedia_hf_task import AskWikipediaHFTask
from tasks.ask_wikipedia_task import AskWikipediaTask
from tasks.index_wikipedia_graph_task import IndexWikipediaGraphTask
from tasks.index_wikipedia_task import IndexWikipediaTask


with TaskDAG(id="wikipedia_es"):
    task = IndexWikipediaTask()

with TaskDAG(id="wikipedia_es_ask"):
    AskWikipediaTask()

with TaskDAG(id="wikipedia_es_ask_hf"):
    AskWikipediaHFTask()

with TaskDAG(id="wikipedia_graph"):
    IndexWikipediaGraphTask()
