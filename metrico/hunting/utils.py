from typing import Any

import random
from logging import getLogger

logger = getLogger(__name__)


def basic_check(exc):
    return str(exc).find("The request cannot be completed because you have exceeded your") != -1


class MultiObjCaller:
    def __init__(self, cls, kwargs: list[dict[str, Any]], check_exc=basic_check):
        self.cls, self.kwargs, self.check_exc = cls, kwargs, check_exc
        random.shuffle(self.kwargs)
        self.obj = self._create_obj()

    def _create_obj(self):
        if not self.kwargs:
            raise Exception("No kwargs to create object")
        kwargs = self.kwargs.pop()
        self.obj = self.cls(**kwargs)
        logger.info("Create object with kwargs=%s", kwargs)
        return self.obj

    def __getattr__(self, name):
        if not hasattr(self.obj, name):
            raise AttributeError(name)

        def wrapper(*args, **kw):
            while True:
                obj_id = id(self.obj)
                try:
                    return getattr(self.obj, name)(*args, **kw)
                except Exception as exc:
                    if self.check_exc(exc):
                        logger.debug("Fail to call %s. exc=%s", name, exc)
                        if obj_id == id(self.obj):
                            self._create_obj()
                    else:
                        break

        return wrapper


if __name__ == "__main__":

    class TestApi:
        def __init__(self, name):
            self.name = name

        def test(self, name: str | None = None):
            if name is not None:
                self.name = name
            if name == "e":
                raise Exception("Oh no...")
            print(self.name)

    api = MultiObjCaller(TestApi, [{"name": "1"}, {"name": "2"}, {"name": "3"}])
    api.test()
    api.test(name="12")
    api.test()

    api.test(name="e")
    api.test()

    api.test(name="e")
    api.test()

    api.test(name="e")
    api.test()
