from logging import getLogger
from pathlib import Path

from metrico.const import DEFAULT_FILENAME
from metrico.core.hunting import MetricoHunter
from metrico.core.hunting.action import update_account, update_media
from metrico.core.triggers import MetricoTrigger
from metrico.core.utils.config import MetricoConfig
from metrico.database import MetricoDB
from metrico.database.query import AccountQuery, BasicQuery, MediaQuery

logger = getLogger(__name__)


class MetricoCore:
    def __init__(self, filename: str | Path | None = None, config: MetricoConfig | None = None):
        self.config: MetricoConfig = config if isinstance(config, MetricoConfig) else MetricoConfig.load(filename)
        self.db: MetricoDB = MetricoDB(self.config.db)  # pylint: disable=invalid-name
        self.hunter: MetricoHunter = MetricoHunter(self.config.hunters)
        self.trigger: MetricoTrigger = MetricoTrigger(self.config.triggers)

    @classmethod
    def default(cls):
        """load default config file"""
        return cls(filename=DEFAULT_FILENAME)

    @classmethod
    def load(cls, filename: str | Path):
        """load config from file"""
        return cls(filename=filename)

    def setup(self) -> int:
        logger.info("setup metrico object")
        self.db.setup()
        return 0

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
                session, hunter=self.hunter, account=account, media_count=media_count, comment_count=comment_count, subscription_count=subscription_count
            )
            session.commit()

    def update_media(self, media_id: int, comment_count: int = -1):
        with self.db.Session() as session:
            media = self.db.get_media(media_id, session=session)
            update_media(session, self.hunter, media, comment_count)
            session.commit()
