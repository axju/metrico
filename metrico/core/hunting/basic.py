# pylint: disable=unused-argument
# mypy: disable-error-code=empty-body
from typing import Any, Iterator

from logging import getLogger

from metrico import schemas

logger = getLogger(__name__)


class BasicHunter(schemas.BasicClassItem):
    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = getLogger(f"{__name__}.{self.__class__.__name__}")

    def analyze(self, value: Any, amount: int = 10, full: bool = False) -> Iterator[schemas.Account | schemas.Media]:
        ...

    def get_account_data(self, identifier: str) -> schemas.Account | None:
        ...

    def get_media_data(self, identifier: str) -> schemas.Media | None:
        ...

    def iter_account_media(self, identifier: str, amount: int = 0) -> Iterator[schemas.Media]:
        ...

    def iter_account_subscriptions(self, identifier: str, amount: int = 0) -> Iterator[schemas.Subscription]:
        ...

    def iter_media_comments(self, identifier: str, amount: int = 0) -> Iterator[schemas.MediaComment]:
        ...
