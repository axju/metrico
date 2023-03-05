from logging import Formatter, StreamHandler, getLogger


def config_logger(verbose: int, name: str | None = None):
    logger = getLogger(name)
    level = 40 - verbose * 10 if verbose <= 3 else 30
    logger.setLevel(level)
    handler = StreamHandler()
    handler.setLevel(level)
    formatter = Formatter("%(asctime)s - %(name)20s - %(levelname)6s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
