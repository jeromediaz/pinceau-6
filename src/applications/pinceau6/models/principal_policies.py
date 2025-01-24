from typing import List, ClassVar, Set

from applications.pinceau6.models.policy import Policy
from core.models.a_model import AModel


class PrincipalPolicies(AModel):
    META_MODEL = "p6_principal_policies"

    HIDDEN_FIELDS_LIST: ClassVar[Set[str]] = {"policies"}

    name: str
    principal: str

    policies: List[Policy]
