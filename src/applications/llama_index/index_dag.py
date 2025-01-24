from applications.llama_index.tasks.li_format_node_batch_task import (
    LiFormatNodeBatchTask,
)
from applications.llama_index.tasks.li_llm import LLMPrepareTask
from applications.llama_index.tasks.li_llm_predict import LLMPredictTask
from applications.llama_index.tasks.li_retriever_task import LiRetrieverTask
from applications.llama_index.tasks.li_score_node_as_text_task import (
    PassthroughTask,
)
from core.tasks.task_dag import TaskDAG

with TaskDAG(id="test_retriever_llm", required_worker_tag="MM1"):
    retriever_task = LiRetrieverTask(id="retriever")
    format_nodes = LiFormatNodeBatchTask(id="format_nodes")

    llm = LLMPrepareTask(id="get_llm", is_passthrough=True)
    predict = LLMPredictTask(id="llm_predict_task")
    vmt = PassthroughTask(id="value_mapper_task")

    llm >> predict >> vmt >> retriever_task >> format_nodes

with TaskDAG(id="test_retriever"):
    retriever_task = LiRetrieverTask(id="retriever")
    format_nodes = LiFormatNodeBatchTask(id="format_nodes")

    retriever_task >> format_nodes
