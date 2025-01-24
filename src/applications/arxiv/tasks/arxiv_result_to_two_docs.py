import hashlib
import logging
import os
import shutil
import urllib
from pathlib import Path
from typing import TYPE_CHECKING

import arxiv
from llama_index.core import SimpleDirectoryReader, Document

from applications.arxiv.tasks.index_arxiv_result import IndexArxivResult
from core.tasks.types import TaskData, TaskDataAsyncIterator

logging.basicConfig(level=logging.DEBUG)

PAPERS_DOWNLOAD_FOLDER = ".papers"

if TYPE_CHECKING:
    from core.context.context import Context


def _hacky_hash(some_string):
    return hashlib.md5(some_string.encode("utf-8")).hexdigest()


class ArxivResultToTwoDocsTask(IndexArxivResult):

    async def _generator_process(
        self, context: "Context", data_in: TaskData
    ) -> TaskDataAsyncIterator:

        data_object = self.input_object(data_in)

        result: arxiv.Result = data_object.result

        metadata = {
            "arxiv id": result.entry_id,
            "Title of this paper": result.title,
            "Authors": ", ".join([a.name for a in result.authors]),
            "Date published": result.published.strftime("%m/%d/%Y"),
            "Date updated": result.updated.strftime("%m/%d/%Y"),
            "Primary category": result.primary_category,
            "Categories": ", ".join(result.categories),
        }

        filename = f"{_hacky_hash(result.title)}.pdf"
        os.makedirs(PAPERS_DOWNLOAD_FOLDER, exist_ok=True)
        try:
            written_path = Path(
                result.download_pdf(dirpath=PAPERS_DOWNLOAD_FOLDER, filename=filename)
            )

            yield {
                "document": Document(
                    doc_id=result.entry_id, text=result.summary, extra_info=metadata
                )
            }

            def get_paper_metadata(*args):
                return metadata

            docs = SimpleDirectoryReader.load_file(written_path, get_paper_metadata, {})
            shutil.rmtree(PAPERS_DOWNLOAD_FOLDER)

            doc = docs[0]
            metadata = {**doc.metadata}
            doc.id_ = f"{result.entry_id}"
            yield {
                "document": Document(
                    doc_id=f"{result.entry_id}",
                    text=doc.text,
                    extra_info=metadata,
                )
            }

        except urllib.error.HTTPError:
            pass
