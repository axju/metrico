# pylint: disable=unused-argument
# mypy: disable-error-code=empty-body
from typing import Any, Iterator

from logging import getLogger

from metrico import models

logger = getLogger(__name__)


class BasicHunter(models.BasicClassItem):
    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = getLogger(f"{__name__}.{self.__class__.__name__}")

    def analyze(self, value: Any, amount: int = 10, full: bool = False) -> Iterator[models.Account | models.Media]:
        ...

    def get_account_data(self, identifier: str) -> models.Account | None:
        ...

    def get_media_data(self, identifier: str) -> models.Media | None:
        ...

    def iter_account_media(self, identifier: str, amount: int = 0) -> Iterator[models.Media]:
        ...

    def iter_account_subscriptions(self, identifier: str, amount: int = 0) -> Iterator[models.Subscription]:
        ...

    def iter_media_comments(self, identifier: str, amount: int = 0) -> Iterator[models.MediaComment]:
        ...
