from typing import Optional, ClassVar

from core.models.a_model import AModel


class Character(AModel):
    META_MODEL: ClassVar[str] = "character"

    login: str
    display_name: str
    avatar: Optional[str] = None

