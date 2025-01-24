import asyncio
import datetime
import logging
from enum import Enum
from typing import TYPE_CHECKING, Optional, cast

import arxiv
from pydantic import BaseModel
from pydantic import Field

from core.database.mongodb import MongoDBHandler
from core.tasks.task import Task
from core.tasks.types import TaskData, TaskDataAsyncIterator
from misc.arxiv_client import Client
from models.ingestion import Ingestion

if TYPE_CHECKING:
    from core.context.context import Context

logging.basicConfig(level=logging.DEBUG)

INGESTION_TABLE = "ingestion3"


class SearchMode(Enum):
    RELEVANCE = "RELEVANCE"
    UPDATED_DOCS = "UPDATED_DOCS"


class SearchArxivTask(Task["SearchArxivTask.InputModel"]):

    class OutputModel(BaseModel):
        class Config:
            arbitrary_types_allowed = True

        subject: str
        result: arxiv.Result
        ingestion: Ingestion

    class InputModel(BaseModel):
        subject: str

    class UI(BaseModel):
        skipped_count: str = Field(title="Arxiv document skipped")
        ingest_count: str = Field(title="Arxiv ingested document")
        current_article: str = Field(title="Arxiv current article")
        ingest_state: str = Field(title="Search ingestion state")

    class Parameters(BaseModel):
        max_ingestion_per_run: int = Field(-1, ge=-1)
        logging_steps: int = Field(1, ge=1)
        collection: str = Field(default="ingestion3")
        db_link: str = Field(default="mongodb")
        database: str = Field(default="pinceau6")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._ingestion: Optional[Ingestion] = None
        self._skipped_count = 0
        self._ingestion_count = 0
        self._search_mode: SearchMode = SearchMode.UPDATED_DOCS

    async def _generator_process_before(
        self, context: "Context", data_in: TaskData
    ) -> TaskData:

        params = cast(SearchArxivTask.Parameters, self.merge_params(data_in))

        data_input_object = self.input_object(data_in)

        subject = data_input_object.subject.lower()

        now = datetime.datetime.now()
        db_handler = MongoDBHandler.from_default(
            context, db_link=params.db_link, database=params.database
        )
        ingestion: Ingestion = db_handler.load_one(
            params.collection, {"data.keyword": subject}
        )

        if not ingestion:
            ingestion = Ingestion(
                data={"keyword": subject},
                pipeline="arxiv",
                first_ingestion_date=now,
                last_ingestion_run_date=now,
            )
        else:
            ingestion.last_ingestion_run_date = now

        db_handler.save_object(context, ingestion, params.collection)

        self._ingestion = ingestion

        return data_in

    async def _generator_process_after(
        self, context: "Context", data_in: TaskData
    ) -> TaskData:

        await asyncio.sleep(3)  # TODO: find another way
        params = cast(SearchArxivTask.Parameters, self.merge_params(data_in))

        db_handler = MongoDBHandler.from_default(
            context, db_link=params.db_link, database=params.database
        )

        if self._ingestion:
            db_handler.save_object(context, self._ingestion, params.collection)

        return data_in

    async def _generator_process(
        self, context: "Context", data_input: TaskData
    ) -> TaskDataAsyncIterator:
        data_input_object = self.input_object(data_input)

        await asyncio.sleep(0)

        big_slow_client = Client(page_size=2000, delay_seconds=3.0, num_retries=5)
        subject = data_input_object.subject.lower()

        ingestion = self._ingestion

        if not ingestion:
            return

        await context.event(
            self,
            "data",
            {
                "skipped_count": f"{self._skipped_count:_}",
                "ingest_count": f"{self._ingestion_count:_}",
                "current_article": "-",
                "ingest_state": f"{len(ingestion.documents)} / ??",
            },
        )

        params: SearchArxivTask.Parameters = cast(
            SearchArxivTask.Parameters, self.merge_params(data_input)
        )

        try:
            documents = ingestion.documents
            if self._search_mode == SearchMode.RELEVANCE:

                for result, result_index, result_total in big_slow_client.results(
                    arxiv.Search(query=subject)
                ):
                    if result_total == 0:
                        break

                    if result_index % params.logging_steps == 0:
                        await context.event(
                            self,
                            "data",
                            {
                                "ingest_state": f"{len(ingestion.documents)} / {result_total}"
                            },
                        )

                    ingestion_data = documents.get(result.entry_id)
                    if ingestion_data and ingestion_data.date == result.updated:
                        self._skipped_count += 1

                        if result_index % params.logging_steps == 0:
                            await context.event(
                                self,
                                "data",
                                {"skipped_count": str(self._skipped_count)},
                            )

                            await self.set_progress(
                                context, float(result_index) / float(result_total)
                            )

                        continue

                    if result_index % params.logging_steps == 0:
                        # context.task_data(self, "current_article", result.title)
                        await context.event(
                            self,
                            "data",
                            {"current_article": result.title},
                        )

                    yield {
                        "subject": subject,
                        "result": result,
                        "ingestion": self._ingestion,
                        **data_input,
                    }

                    self._ingestion_count += 1

                    if (
                        params.max_ingestion_per_run > 0
                        and self._ingestion_count >= params.max_ingestion_per_run
                    ):
                        break
            else:
                current_doc_count = len(documents)
                search_ingested_docs = 0
                for result, result_index, result_total in big_slow_client.results(
                    arxiv.Search(
                        query=subject, sort_by=arxiv.SortCriterion.LastUpdatedDate
                    )
                ):
                    if result_total == 0:
                        break

                    if result_index % params.logging_steps == 0:
                        await context.event(
                            self,
                            "data",
                            {
                                "ingest_state": f"> {len(ingestion.documents)} / {result_total}"
                            },
                        )

                    ingestion_data = documents.get(result.entry_id)

                    if ingestion_data and ingestion_data.date == result.updated:

                        if result_total == current_doc_count:
                            # same update date + same number of results: all docs are already ingested!
                            self._skipped_count += (
                                current_doc_count - search_ingested_docs
                            )

                            if result_index % params.logging_steps == 0:
                                await context.event(
                                    self,
                                    "data",
                                    {"skipped_count": f"{self._skipped_count:_}"},
                                )

                                await self.set_progress(context, 1.0)

                            break

                        self._skipped_count += 1

                        if result_index % params.logging_steps == 0:
                            await context.event(
                                self,
                                "data",
                                {"skipped_count": f"{self._skipped_count:_}"},
                            )

                            await self.set_progress(
                                context, float(result_index) / float(result_total)
                            )

                        continue

                    # context.task_data(self, "current_article", result.title)
                    if result_index % params.logging_steps == 0:
                        await context.event(
                            self,
                            "data",
                            {"current_article": result.title},
                        )

                    yield {
                        "subject": subject,
                        "result": result,
                        "ingestion": self._ingestion,
                        **data_input,
                    }

                    self._ingestion_count += 1
                    current_doc_count += 1
                    search_ingested_docs += 1

                    if result_index % params.logging_steps == 0:
                        await context.event(
                            self,
                            "data",
                            {"ingest_count": f"{self._ingestion_count:_}"},
                        )

                        await self.set_progress(
                            context, float(result_index) / float(result_total)
                        )

                    if (
                        params.max_ingestion_per_run > 0
                        and self._ingestion_count >= params.max_ingestion_per_run
                    ):
                        break
        except Exception as e:
            print(e)

        await self.set_progress(context, 1.0)
        print("FINISHED")
