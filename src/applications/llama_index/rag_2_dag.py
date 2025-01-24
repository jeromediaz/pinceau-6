from applications.llama_index.tasks.li_chained_retriever_task import (
    LiChainedRetrieverTask,
)
from applications.llama_index.tasks.li_chat_history_list import (
    ChatListTask,
    ChatBufferListTask,
    ChatHistoryStringTask,
)
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

with TaskDAG(id="test_rag_no_llm", required_worker_tag="MM1"):
    llm = LLMPrepareTask(id="get_llm", is_passthrough=True, label="Select LLM")

    condense = LLMPredictTask(id="llm_condense", label="Condense")
    answer_generation = LLMPredictTask(
        id="answer_generation", label="Answer Generation"
    )

    condense_predict_log = PassthroughTask(
        id="condense_predict_log", label="Log condensed"
    )
    keyword_retriever = LiRetrieverTask(
        id="keyword_retriever", label="Summary retriever"
    )
    vector_retriever = LiChainedRetrieverTask(
        id="vector_retriever", label="Content retriever"
    )

    chat_list = ChatListTask(id="chat_list", label="Extract chat list")
    chat_buffer = ChatBufferListTask(id="chat_buffer", label="Crop chat list")
    chat_history_str = ChatHistoryStringTask(id="history_str", label="Chat list as str")

    format_nodes = LiFormatNodeBatchTask(id="format_nodes", label="Prepare context")

    chat_list >> chat_buffer >> chat_history_str >> condense

    llm >> [chat_buffer, condense, answer_generation]
    condense >> vector_retriever
    condense >> condense_predict_log >> keyword_retriever

    keyword_retriever >> vector_retriever

    vector_retriever >> format_nodes

    format_nodes >> answer_generation
    condense >> answer_generation
