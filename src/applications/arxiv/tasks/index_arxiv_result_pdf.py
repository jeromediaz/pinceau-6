import hashlib
import logging
import os
import shutil
from pathlib import Path
from typing import Mapping, Any

import arxiv
from llama_index.core import SimpleDirectoryReader, Document

from applications.arxiv.tasks.index_arxiv_result import IndexArxivResult
from core.database.mongodb import MongoDBHandler
from models.ingestion import IngestedDocument

logging.basicConfig(level=logging.DEBUG)

PAPERS_DOWNLOAD_FOLDER = ".papers"


def _hacky_hash(some_string):
    return hashlib.md5(some_string.encode("utf-8")).hexdigest()


class IndexArxivResultPDF(IndexArxivResult):

    async def _process(self, context, data_in: Mapping[str, Any]) -> Mapping[str, Any]:
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
        written_path = Path(
            result.download_pdf(dirpath=PAPERS_DOWNLOAD_FOLDER, filename=filename)
        )

        index_vector_store = data_in["index"]()
        ingestion = data_in["ingestion"]

        summary_doc = Document(
            doc_id=result.entry_id, text=result.summary, extra_info=metadata
        )

        def get_paper_metadata(*args):
            return metadata

        docs = SimpleDirectoryReader.load_file(written_path, get_paper_metadata, {})
        shutil.rmtree(PAPERS_DOWNLOAD_FOLDER)
        for doc in docs:
            metadata = {**doc.metadata}
            doc.id_ = f"{result.entry_id}"
            work_doc = Document(
                doc_id=f"{result.entry_id}",
                text=doc.text,
                extra_info=metadata,
            )

            index_vector_store.insert_vector(work_doc)

        index_vector_store.insert_text(summary_doc)

        ingestion.documents[result.entry_id] = IngestedDocument(date=result.updated)
        db_handler = MongoDBHandler.from_default(context)
        db_handler.update_object(context, ingestion, "ingestion")

        del result

        return {}
