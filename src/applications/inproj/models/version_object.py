from typing import Optional

from pydantic import BaseModel


class VersionObject(BaseModel):
    text: str
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    @classmethod
    def from_pypy_text(cls, text: str) -> "VersionObject":
        from packaging.version import Version as PyPIVersion

        ver = PyPIVersion(text)

        return VersionObject(
            text=text, major=ver.major, minor=ver.minor, patch=ver.micro
        )
