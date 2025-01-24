from enum import Enum
from typing import List

from core.models.a_model import AModel
from ui.helper import FieldOptions, P6Field


class Effect(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class Policy(AModel):

    META_MODEL = "p6_policy"
    IS_ABSTRACT = True

    # effect: Effect = Effect.ALLOW
    resource: str = P6Field(
        "*", options=FieldOptions.FULL_WIDTH | FieldOptions.MULTILINE
    )
    actions: List[str] = []
