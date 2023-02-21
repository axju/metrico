from typing import Generic, TypeVar

import importlib
from importlib.metadata import entry_points
from logging import Logger, getLogger

from metrico.models import BasicClassConfig, BasicClassItem

from .misc import update_list

T = TypeVar("T", bound=BasicClassItem)


class DynamicClassDict(Generic[T]):
    DEFAULT_CLS: dict[str, type[T]] = {}
    ENTRY_POINT: str = ""

    def __init__(self, config: dict[str, BasicClassConfig]):
        self.logger: Logger = getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config: dict[str, BasicClassConfig] = config
        self.cls: dict[str, type[T]] = dict(self.DEFAULT_CLS)
        self.objs: dict[str, T] = {}
        self._load_cls_from_entry_points()
        self._load_cls_from_conf()

    def __getitem__(self, name: str) -> T:
        if name in self.objs:
            return self.objs[name]

        if name in self.cls:
            return self.create_obj(name)

        raise Exception(f"Fail to get object for {name}")

    def _load_cls_from_str(self, name: str, cls_str: str):
        try:
            module_str, cls_name = cls_str.split(":")
            module = importlib.import_module(module_str)
            self.cls[name] = getattr(module, cls_name)
        except Exception:
            self.logger.exception("Fail to load class for %s! Check your config file ;-)", name)

    def _load_cls_from_conf(self):
        """
        load all hunters classes
        """
        for name, hunter_config in self.config.items():
            if cls_str := hunter_config.cls:
                self._load_cls_from_str(name, cls_str)
        return self.cls

    def _load_cls_from_entry_points(self):
        for entry_point in entry_points().select(group=self.ENTRY_POINT):
            self.cls[entry_point.name] = entry_point.load()

    def create_obj(self, name: str):
        if name in self.config:
            self.objs[name] = self.cls[name](self.config[name].config)
        else:
            self.objs[name] = self.cls[name]({})
        return self.objs[name]

    def items(self):
        for name in self.cls:
            yield name, self[name]
