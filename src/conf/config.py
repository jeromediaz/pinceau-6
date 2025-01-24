import logging
import os
import platform
from enum import Enum
from typing import Any, Dict, Optional, TypeVar

from dotenv import dotenv_values

from misc.singleton_meta import SingletonMeta

ConfigMap = Dict[str, str | None]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


T = TypeVar("T")


class RunMode(Enum):
    API = 0
    WORKER = 1
    TEST = 2


class Config(object, metaclass=SingletonMeta):

    def __init__(self) -> None:
        logger.info("Initializing config object")
        self._platform_name = platform.node()

        self.os_env_var = {
            k[3:]: v for k, v in os.environ.items() if k.startswith("P6_")
        }

        self._run_mode: RunMode = getattr(
            RunMode, self.os_env_var.get("RUN_MODE", "API").upper()
        )

        self.root_var = Config.load_from_file()

        if "ENVIRONMENT" in self.os_env_var:
            self._environment = self.os_env_var.get("ENVIRONMENT")
        else:
            self._environment = self.root_var.get("ENVIRONMENT")

        self.env_var = Config.load_from_file(self.environment)

        self.platform_var = Config.load_from_file(self._platform_name)

        self.final_var = {
            **self.os_env_var,
            **self.root_var,
            **self.platform_var,
            **self.env_var,
        }
        logger.debug("Loaded params %s", self.final_var)
        print(self.final_var)

    @property
    def run_mode(self) -> RunMode:
        return self._run_mode

    @staticmethod
    def load_from_file(prefix: Optional[str] = None) -> ConfigMap:

        if not prefix:
            file_path = "conf/.env"
        else:
            work_prefix = prefix.replace(".", "-").lower()
            file_path = f"conf/.{work_prefix}.env"
        logger.info("Loading config from %s", file_path)
        print(f"Loading config from {os.path.abspath(file_path)}")
        values = dotenv_values(file_path)

        return values

    @property
    def environment(self):
        return self._environment

    @property
    def platform_name(self) -> str:
        return self._platform_name

    def __getitem__(self, item: str) -> Any:
        return self.final_var[item]

    def get(self, item: str, coerce=None, default=None) -> Any:  # TODO: type hinting
        raw_value = self.final_var.get(item)

        if raw_value is None:
            return default

        return coerce(raw_value) if coerce else raw_value
