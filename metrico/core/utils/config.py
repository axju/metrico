from logging import getLogger
from pathlib import Path

from pydantic import BaseSettings

from metrico.schemas import BasicClassConfig, DatabaseConfig

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore


logger = getLogger(__name__)


class MetricoConfig(BaseSettings):
    db: DatabaseConfig = DatabaseConfig()
    triggers: dict[str, BasicClassConfig] = {}
    hunters: dict[str, BasicClassConfig] = {}

    class Config:
        extra = "ignore"

    @classmethod
    def load(cls, path: str | Path | None):
        if path is None:
            return cls()
        file = Path(path)
        with file.open("rb") as toml_file:
            data = tomllib.load(toml_file)
        return cls.parse_obj(data)
