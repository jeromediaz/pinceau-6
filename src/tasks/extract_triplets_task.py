from typing import Mapping, Any, TYPE_CHECKING, List, cast

from pydantic import BaseModel

from core.tasks.task import Task

if TYPE_CHECKING:
    from core.context.context import Context


class ExtractTripletsTask(Task):
    class Parameters(BaseModel):
        max_length: int = 128

    class InputModel(BaseModel):
        response: str

    class OutputModel(BaseModel):
        triplets: List[List[str]]

    async def _process(
        self, context: "Context", data_input: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        params = cast(ExtractTripletsTask.Parameters, self.merge_params(data_input))
        input_data = self.input_object(data_input)

        knowledge_strs = input_data.response.strip().split("\n")
        results = []
        for text in knowledge_strs:
            if "(" not in text or ")" not in text or text.index(")") < text.index("("):
                # skip empty lines and non-triplets
                continue
            triplet_part = text[text.index("(") + 1 : text.index(")")]
            tokens = triplet_part.split(",")
            if len(tokens) != 3:
                continue

            if any(len(s.encode("utf-8")) > params.max_length for s in tokens):
                # We count byte-length instead of len() for UTF-8 chars,
                # will skip if any of the tokens are too long.
                # This is normally due to a poorly formatted triplet
                # extraction, in more serious KG building cases
                # we'll need NLP models to better extract triplets.
                continue

            subj, pred, obj = map(str.strip, tokens)
            if not subj or not pred or not obj:
                # skip partial triplets
                continue
            results.append((subj, pred, obj))

        return {**data_input, "triplets": results}
