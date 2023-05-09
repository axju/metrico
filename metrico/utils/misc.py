from typing import Any, Callable

from logging import Formatter, StreamHandler, getLogger
from threading import Thread
from time import sleep

logger = getLogger(__name__)


def config_logger(verbose: int, name: str | None = None):
    _logger = getLogger(name)
    level = 40 - verbose * 10 if verbose <= 3 else 30
    _logger.setLevel(level)
    handler = StreamHandler()
    handler.setLevel(level)
    formatter = Formatter("%(asctime)s - %(name)20s - %(levelname)6s - %(message)s")
    handler.setFormatter(formatter)
    _logger.addHandler(handler)


def thread_call(obj_ids, update_func, kwargs, threads_count) -> bool:
    threads: list[Thread] = []
    success: bool = False
    try:
        for obj_id in obj_ids:
            while len(threads) > threads_count - 1:
                threads = [t for t in threads if t.is_alive()]
                sleep(0.1)

            thread = Thread(target=update_func, args=(obj_id,), kwargs=kwargs)
            thread.start()
            threads.append(thread)
    except:
        logger.exception("exception in thread loop ")
        success = False

    logger.info("waiting for all threads to end")
    for thread in threads:
        thread.join()
    return success


def update_list(ids: list[int], func: Callable[[int, int, int, int], Any] | Callable[[int, int], Any], threads: int = 0, **kwargs: Any) -> bool:
    logger.info("update list with threads=%i, kwargs=%s", threads, kwargs)
    if isinstance(threads, int) and threads > 1:
        return thread_call(ids, func, kwargs, threads)
    for obj_id in ids:
        func(obj_id, **kwargs)  # type: ignore
    return True
