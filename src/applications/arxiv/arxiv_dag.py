from applications.arxiv.tasks.arxiv_ingestion_confirm import ArxivIngestionConfirm
from applications.arxiv.tasks.arxiv_result_to_two_docs import ArxivResultToTwoDocsTask
from applications.arxiv.tasks.index_arxiv_result_pdf import IndexArxivResultPDF
from applications.arxiv.tasks.list_arxiv_search_cat_task import ListArxivSearchCatTask
from applications.arxiv.tasks.search_arxiv_task import SearchArxivTask
from applications.arxiv.tasks.store_arxiv_title_category import (
    StoreArxivTitleCategory,
    ArxivTitleCategoryPrepareIndexTask,
)
from applications.arxiv.tasks.title_classification_evaluation_task import (
    TitleClassificationEvaluationTask,
)
from applications.arxiv.tasks.title_classification_task import TitleClassificationTask
from applications.huggingface.tasks.train_task import (
    ArxivTrainPrepareTask,
    ArxivTrainTask,
    SplitData,
)
from applications.llama_index.tasks.li_ingest_document_task import LiIngestDocumentTask
from conf.config import Config
from core.tasks.task_dag import TaskDAG
from tasks.agent_mongodb_upsert import AgentMongoDBUpsert
from tasks.build_two_steps_vector_index_task import BuildTwoStepsVectorIndexTask
from tasks.round_robin_task import RoundRobinTask

with TaskDAG(id="arxiv"):
    search = SearchArxivTask(id="search_arxiv_task")
    content = IndexArxivResultPDF(id="index_arxiv_result")

    search >> content

with TaskDAG(id="arxiv-2", tags=["RAG"], required_worker_tag="MM1"):
    index = BuildTwoStepsVectorIndexTask(
        id="build_two_steps_vector_index", es_url=Config()["ES_URL"]
    )
    search = SearchArxivTask(id="search_arxiv_task")
    content = IndexArxivResultPDF(id="index_arxiv_result")

    search >> content
    index >> content
    # search >> summary

with TaskDAG(id="arxiv-3", tags=["RAG"], required_worker_tag="MM1"):
    search = SearchArxivTask(id="search_arxiv_task")
    as_docs = ArxivResultToTwoDocsTask(id="arxiv_to_docs")
    round_robin = RoundRobinTask(id="round_robin")

    summary = LiIngestDocumentTask(id="ingest_summary_task", label="ingest summary")
    pdf = LiIngestDocumentTask(id="ingest_pdf_task", label="ingest content")

    search >> as_docs >> round_robin >> [summary, pdf]

with TaskDAG(id="search-arxiv"):
    index = BuildTwoStepsVectorIndexTask(
        index_name="arxiv-articles", es_url=Config()["ES_URL"]
    )
    task = IndexArxivResultPDF()

    index >> task

with TaskDAG(
    id="retrieve_docs_2step_vector_index", tags=["RAG"], required_worker_tag="MM1"
):
    index = BuildTwoStepsVectorIndexTask(
        id="build_two_steps_vector_index", es_url=Config()["ES_URL"]
    )


with TaskDAG(id="search-arxiv-2"):
    index = BuildTwoStepsVectorIndexTask(
        index_name="arxiv-articles-2", es_url=Config()["ES_URL"]
    )
    task = IndexArxivResultPDF()

    index >> task

with TaskDAG(id="build_title_category_index", required_worker_tag="MM1"):
    arxiv_list_search_cat = ListArxivSearchCatTask(id="arxiv_cat")
    search = SearchArxivTask(id="arxiv_search")
    prepare_index = ArxivTitleCategoryPrepareIndexTask(id="arxiv_prepare_index")
    prepare = StoreArxivTitleCategory(id="prepare_data")
    store = AgentMongoDBUpsert(id="store_data")
    confirm = ArxivIngestionConfirm(id="arxiv_ingestion_confirm")

    arxiv_list_search_cat >> search
    search ^ prepare_index
    search >> prepare
    prepare >> store
    store >> confirm


with TaskDAG(
    id="train_model", required_worker_tag="MM1", tags=["arxiv", "saaswedo", "ml"]
):

    split_data = SplitData(id="split_data", requires_trained_model=False)

    prepare_ds = ArxivTrainPrepareTask(id="prepare_ds")

    train = ArxivTrainTask(id="train")

    split_data >> prepare_ds >> train


with TaskDAG(
    id="test_model", required_worker_tag="MM1", tags=["arxiv", "saaswedo", "ml"]
):
    split_data = SplitData(id="split_data", requires_trained_model=True)

    test = TitleClassificationTask(id="title_classification")

    split_data >> test

with TaskDAG(
    id="evaluate_model", required_worker_tag="MM1", tags=["arxiv", "saaswedo", "ml"]
):
    split_data = SplitData(id="split_data", requires_trained_model=True)

    evaluate = TitleClassificationEvaluationTask(id="title_classification_evaluation")

    split_data >> evaluate
