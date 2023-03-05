from logging import getLogger

from metrico.core.utils import DynamicClassDict

from .simple import SimpleTrigger

logger = getLogger(__name__)


class MetricoTrigger(DynamicClassDict[SimpleTrigger]):
    DEFAULT_CLS = {
        "init": SimpleTrigger,
    }
    ENTRY_POINT = "metrico.triggers"

    def create_obj(self, name: str):
        self.objs[name] = self.cls[name](name, self.config[name].config)
        return self.objs[name]
