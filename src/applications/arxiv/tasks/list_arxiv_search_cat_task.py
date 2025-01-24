import asyncio
import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from core.tasks.task import Task
from core.tasks.types import TaskData, TaskDataAsyncIterator

if TYPE_CHECKING:
    from core.context.context import Context

logging.basicConfig(level=logging.DEBUG)

CATEGORIES = [
    "cs.AI",
    "cs.AR",
    "cs.CC",
    "cs.CE",
    "cs.CG",
    "cs.CL",
    "cs.CR",
    "cs.CV",
    "cs.CY",
    "cs.DB",
    "cs.DC",
    "cs.DL",
    "cs.DM",
    "cs.DS",
    "cs.ET",
    "cs.FL",
    "cs.GL",
    "cs.GR",
    "cs.GT",
    "cs.HC",
    "cs.IR",
    "cs.IT",
    "cs.LG",
    "cs.LO",
    "cs.MA",
    "cs.MM",
    "cs.MS",
    "cs.NA",
    "cs.NE",
    "cs.NI",
    "cs.OH",
    "cs.OS",
    "cs.PF",
    "cs.PL",
    "cs.RO",
    "cs.SC",
    "cs.SD",
    "cs.SE",
    "cs.SI",
    "cs.SY",
    "econ.EM",
    "econ.GN",
    "econ.TH",
    "eess.AS",
    "eess.IV",
    "eess.SP",
    "eess.SY",
    "math.AC",
    "math.AG",
    "math.AP",
    "math.AT",
    "math.CA",
    "math.CO",
    "math.CT",
    "math.CV",
    "math.DG",
    "math.DS",
    "math.FA",
    "math.GM",
    "math.GN",
    "math.GR",
    "math.GT",
    "math.HO",
    "math.IT",
    "math.KT",
    "math.LO",
    "math.MG",
    "math.MP",
    "math.NA",
    "math.NT",
    "math.OA",
    "math.OC",
    "math.PR",
    "math.QA",
    "math.RA",
    "math.RT",
    "math.SG",
    "math.SP",
    "math.ST",
    "astro-ph.CO",
    "astro-ph.EP",
    "astro-ph.GA",
    "astro-ph.HE",
    "astro-ph.IM",
    "astro-ph.SR",
    "cond-mat.dis-nn",
    "cond-mat.mes-hall",
    "cond-mat.mtrl-sci",
    "cond-mat.other",
    "cond-mat.quant-gas",
    "cond-mat.soft",
    "cond-mat.stat-mech",
    "cond-mat.str-el",
    "cond-mat.supr-con",
    "gr-qc",
    "hep-ex",
    "hep-lat",
    "hep-ph",
    "hep-th",
    "math-ph",
    "nlin.AO",
    "nlin.CD",
    "nlin.CG",
    "nlin.PS",
    "nlin.SI",
    "nucl-ex",
    "nucl-th",
    "physics.acc-ph",
    "physics.ao-ph",
    "physics.app-ph",
    "physics.atm-clus",
    "physics.atom-ph",
    "physics.bio-ph",
    "physics.chem-ph",
    "physics.class-ph",
    "physics.comp-ph",
    "physics.data-an",
    "physics.ed-ph",
    "physics.flu-dyn",
    "physics.gen-ph",
    "physics.geo-ph",
    "physics.hist-ph",
    "physics.ins-det",
    "physics.med-ph",
    "physics.optics",
    "physics.plasm-ph",
    "physics.pop-ph",
    "physics.soc-ph",
    "physics.space-ph",
    "quant-ph",
    "q-bio.BM",
    "q-bio.CB",
    "q-bio.GN",
    "q-bio.MN",
    "q-bio.NC",
    "q-bio.OT",
    "q-bio.PE",
    "q-bio.QM",
    "q-bio.SC",
    "q-bio.TO",
    "q-fin.CP",
    "q-fin.EC",
    "q-fin.GN",
    "q-fin.MF",
    "q-fin.PM",
    "q-fin.PR",
    "q-fin.RM",
    "q-fin.ST",
    "q-fin.TR",
    "stat.AP",
    "stat.CO",
    "stat.ME",
    "stat.ML",
    "stat.OT",
    "stat.TH",
]


class ListArxivSearchCatTask(Task):

    class UI(BaseModel):
        category: str = Field(title="Arxiv category")

    class OutputModel(BaseModel):
        subject: str

    def __init__(self, *args, **kwargs):
        kwargs.pop("is_passthrough", True)
        super().__init__(*args, is_passthrough=True, **kwargs)

    async def _generator_process(
        self, context: "Context", data_input: TaskData
    ) -> TaskDataAsyncIterator:

        await context.event(self, "data", {"category": "-"})

        total = len(CATEGORIES)
        for i, cat in enumerate(CATEGORIES):
            yield {**data_input, "subject": f"cat:{cat}"}

            await context.event(self, "data", {"category": f"{cat} {i + 1}/{total}"})
            await asyncio.sleep(3)  # TO CONFORM TO arxiv policy

        # context.on_event(context, self, "data", {"category": "-"})
