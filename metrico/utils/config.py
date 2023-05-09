import logging.config
import os
from logging import getLogger
from pathlib import Path

from pydantic import BaseSettings

from metrico.const import DEFAULT_FILENAMES
from metrico.schemas import DatabaseConfig, HuntingConfig

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore


logger = getLogger(__name__)


class MetricoConfig(BaseSettings):
    db: DatabaseConfig = DatabaseConfig()
    hunting: HuntingConfig = HuntingConfig()

    logger: dict = {}

    class Config:
        extra = "ignore"

    @classmethod
    def load(cls, path: str | Path):
        """
        Load settings from path | str or load the default settings

        :param path: The config file path
        """

        file = Path(path)
        if not file.is_file():
            logger.warning("File %s not exist! Load default settings", file)
            return cls()

        with file.open("rb") as toml_file:
            data = tomllib.load(toml_file)
        return cls.parse_obj(data)

    @classmethod
    def default(cls):
        """
        Load default config form default path or environment variable (METRICO_CONF_PATH)
        """
        if env_path := os.environ.get("METRICO_CONF_PATH"):
            path = Path(env_path)
            if path.is_file():
                return cls.load(path)

        for path in DEFAULT_FILENAMES:
            if path.is_file():
                return cls.load(path)

        return cls()


class ConfigMixin:
    """
    Just a mixin for other classes to load the config object (self.config)

    :param filename: Config file path. Defaults to None.
    :param config: Configuration by object or dict. Defaults to None.
    """

    def __init__(self, filename: str | Path | None = None, config: MetricoConfig | dict | None = None):
        # first load the file or default config
        self.config: MetricoConfig = MetricoConfig.load(filename) if filename is not None else MetricoConfig.default()

        # check the config
        if isinstance(config, (MetricoConfig, dict)):
            self.config.parse_obj(config)

    @classmethod
    def default(cls):
        """
        Load default config form default path or environment variable (METRICO_CONF_PATH)
        """
        if env_path := os.environ.get("METRICO_CONF_PATH"):
            path = Path(env_path)
            if path.is_file():
                return cls(filename=path)

        for path in DEFAULT_FILENAMES:
            if path.is_file():
                return cls(filename=path)

        return cls()

    @classmethod
    def load(cls, path: str | Path):
        """load config from file"""
        return cls(filename=path)


class LoggerMixin(ConfigMixin):
    """Setup a local logger and config global logger from config file.

    :param filename: Config file path. Defaults to None.
    :param config: Configuration by object or dict. Defaults to None.
    """

    def __init__(self, filename: str | Path | None = None, config: MetricoConfig | dict | None = None):
        super().__init__(filename, config)
        if self.config.logger:
            logging.config.dictConfig(self.config.logger)
        self.logger = getLogger(f"{__name__}.{self.__class__.__name__}")
