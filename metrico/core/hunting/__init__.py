from logging import getLogger

from metrico.core.utils import DynamicClassDict

from .basic import BasicHunter

logger = getLogger(__name__)


class MetricoHunter(DynamicClassDict[BasicHunter]):
    DEFAULT_CLS = {
        "dummy": BasicHunter,
    }
    ENTRY_POINT = "metrico.hunters"

    def list_platforms(self):
        return self.cls.keys()
