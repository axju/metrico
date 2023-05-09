from __future__ import annotations

from logging import getLogger
from pathlib import Path

from metrico.const import DEFAULT_FILENAME
from metrico.database import MetricoDB
from metrico.database.query import AccountQuery, BasicQuery, MediaQuery
from metrico.hunting.action import update_account, update_media
from metrico.hunting.hunters.basic import BasicHunter
from metrico.hunting.triggers import MetricoTrigger
from metrico.utils.config import ConfigMixin, MetricoConfig
from metrico.utils.generic import DynamicClassDict

logger = getLogger(__name__)


class MetricoHunters(DynamicClassDict[BasicHunter]):
    DEFAULT_CLS = {
        "dummy": BasicHunter,
    }
    ENTRY_POINT = "metrico.hunters"

    def list_platforms(self):
        return self.cls.keys()


class Hunter(ConfigMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db: MetricoDB = MetricoDB(config=self.config)  # pylint: disable=invalid-name
        self.hunters: MetricoHunters = MetricoHunters(self.config.hunting.hunters)
        self.trigger: MetricoTrigger = MetricoTrigger(self.config.hunting.triggers)

    def run_trigger(self, name: str, **kwargs):
        self.trigger[name].run(self, **kwargs)

    def update_query(self, query: BasicQuery, **kwargs):
        with self.db.Session() as session:
            ids = [item.id for item in query.iter(session)]

        match query:
            case AccountQuery():
                for index in ids:
                    self.update_account(index, **kwargs)
            case MediaQuery():
                for index in ids:
                    self.update_media(index, **kwargs)

    def update_account(self, account_id: int, media_count: int = -1, comment_count: int = -1, subscription_count: int = -1):
        with self.db.Session() as session:
            account = self.db.get_account(account_id, session=session)
            update_account(
                session, hunter=self.hunters, account=account, media_count=media_count, comment_count=comment_count, subscription_count=subscription_count
            )
            session.commit()

    def update_media(self, media_id: int, comment_count: int = -1):
        with self.db.Session() as session:
            media = self.db.get_media(media_id, session=session)
            update_media(session, self.hunters, media, comment_count)
            session.commit()
