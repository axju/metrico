from logging import getLogger

from metrico.utils import DynamicClassDict

from .hunters.basic import BasicHunter
from .hunters.test import TestHunter  # type: ignore
from .hunters.youtube import YoutubeHunter

logger = getLogger(__name__)


class MetricoHunter(DynamicClassDict[BasicHunter]):
    DEFAULT_CLS = {
        "dummy": BasicHunter,
        "test": TestHunter,
        "youtube": YoutubeHunter,
    }
    ENTRY_POINT = "metrico.hunters"

    def list_platforms(self):
        return self.cls.keys()
