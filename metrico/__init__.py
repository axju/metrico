from logging import getLogger

from metrico.database import MetricoDB
from metrico.utils.config import MetricoConfig

logger = getLogger(__name__)

try:
    from metrico.hunting import Hunter
except:
    logger.exception("Fail to load Hunter! Make sure you have install all dependencies! pip install metrico[hunter]")

    class Hunter:
        pass


try:
    from metrico.analyze import Analyzer
except:
    logger.exception("Fail to load Analyzer! Make sure you have install all dependencies! pip install metrico[analyzer]")

    class Analyzer:
        pass


__version__ = "0.0.1"
__all__ = ["MetricoConfig", "MetricoDB", "Hunter", "Analyzer"]
