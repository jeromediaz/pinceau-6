from llama_index.core.prompts.default_prompts import (
    DEFAULT_SUMMARY_PROMPT,
    DEFAULT_KG_TRIPLET_EXTRACT_PROMPT,
)

from applications.llama_index.models.li_node_parser import LiNodeParser
from applications.llama_index.tasks.li_chat_history_list import (
    ChatListTask,
    ChatBufferListTask,
    ChatHistoryStringTask,
)
from applications.llama_index.tasks.li_llm import LLMPrepareTask
from applications.llama_index.tasks.li_llm_predict import LLMPredictTask
from core.tasks.task_dag import TaskDAG
from models.knowledge_graph import KnowledgeGraph
from tasks.a_model_extractor import AModelExtractorTask, AModelUpdatorTask
from tasks.extract_triplets_task import ExtractTripletsTask
from tasks.mongo_object_task import MongoObjectTask
from tasks.range_task import RangeTask
from tasks.round_robin_task import RoundRobinTask
from tasks.wait_task import WaitTask

with TaskDAG(id="test"):
    wait_one = WaitTask(id="one")
    wait_two = WaitTask(5, id="two")
    wait_three = WaitTask(10, id="three")
    wait_four = WaitTask(2, id="four")
    wait_five = WaitTask(5, id="five")

    wait_one >> wait_two
    wait_one >> wait_three
    wait_two >> wait_four
    wait_four >> wait_five
    wait_three >> wait_five


with TaskDAG(id="test_yield", required_worker_tag="MM1"):
    range_test = RangeTask(
        varname="range", start=0, end=5, step=1, label="range", id="range"
    )

    wait_one = WaitTask(1, id="A", label="A 1s")

    round_robin = RoundRobinTask(id="round_robin")

    wait_two = WaitTask(5, id="B", label="B 5s")
    wait_three = WaitTask(10, id="C", label="C 10s")

    wait_4 = WaitTask(10, id="D", label="D 10s")
    wait_5 = WaitTask(5, id="E", label="E 5s")

    wait_a = WaitTask(duration=1, id="BEFORE", label="BEFORE")
    wait_b = WaitTask(duration=1, id="AFTER", label="AFTER")

    range_test >> wait_one

    wait_one >> round_robin

    round_robin >> wait_two >> wait_4
    round_robin >> wait_three >> wait_5

    range_test ^ wait_a
    range_test & wait_b


with TaskDAG(id="llm_test_summary", label="Summary", required_worker_tag="MM1"):
    llm = LLMPrepareTask(id="get_llm", is_passthrough=True)
    predict = LLMPredictTask(DEFAULT_SUMMARY_PROMPT, id="llm_predict_task")
    llm >> predict


with TaskDAG(
    id="llm_test_predict", label="Prediction", required_worker_tag="MM1"
) as dag:
    llm = LLMPrepareTask(id="get_llm", is_passthrough=True)
    predict = LLMPredictTask(id="llm_predict_task")
    llm >> predict

with TaskDAG(
    id="llm_test_predict_history", label="Prediction", required_worker_tag="MM1"
):
    llm = LLMPrepareTask(id="get_llm", is_passthrough=True)
    predict = LLMPredictTask(id="llm_predict_task")
    llm >> predict

    chat_list = ChatListTask(id="chat_list")
    chat_buffer = ChatBufferListTask(id="chat_buffer")
    chat_history_str = ChatHistoryStringTask(id="history_str")

    chat_list >> chat_buffer >> chat_history_str >> predict
    llm >> chat_buffer


with TaskDAG(id="llm_test_triplets", label="Triplets", required_worker_tag="MM1"):
    a = MongoObjectTask(
        KnowledgeGraph.META_MODEL,
        label="Fetch data",
        handler=None,
        id="knowledge_graph_input",
        output_name="model_object",
    )
    a1 = MongoObjectTask(
        LiNodeParser.META_MODEL,
        label="Fetch node parser",
        handler=None,
        id="node_parser",
        input_name="node_parser_id",
        output_name="node_parser",
    )
    b = AModelExtractorTask(
        extract_key="text", output_var="text", id="amodel_extractor"
    )
    llm = LLMPrepareTask(id="get_llm", is_passthrough=True)

    c = LLMPredictTask(DEFAULT_KG_TRIPLET_EXTRACT_PROMPT, id="llm_extract_triplets")
    d = ExtractTripletsTask(id="extract_triplets")
    e = AModelUpdatorTask(id="AModelUpdatorTask")

    llm >> c
    a1 >> b
    a >> b >> c >> d >> e
