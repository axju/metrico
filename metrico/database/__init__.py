from logging import getLogger
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker

from metrico.utils.config import ConfigMixin, MetricoConfig

from .. import schemas
from . import crud, models
from .query import BasicQuery, MediaCommentOrder, MediaCommentQuery, MediaOrder, MediaQuery

logger = getLogger(__name__)


class TriggerAccountCaller:
    def __init__(self, name: str):
        self.name = name

    def __call__(self, _, connection, obj):
        with Session(bind=connection) as session:
            crud.add_to_trigger(session, self.name, account=obj)
            session.commit()


class TriggerMediaCaller:
    def __init__(self, name: str):
        self.name = name

    def __call__(self, _, connection, obj):
        with Session(bind=connection) as session:
            crud.add_to_trigger(session, self.name, media=obj)
            session.commit()


class MetricoDB(ConfigMixin):
    def __init__(self, filename: str | Path | None = None, config: MetricoConfig | dict | None = None):
        super().__init__(filename=filename, config=config)
        # self.config = config
        self.engine, self.Session = self.reload_config()  # pylint: disable=invalid-name

        if trigger := self.config.db.on_create_account_trigger:
            event.listen(models.Account, "after_insert", TriggerAccountCaller(trigger))
        if trigger := self.config.db.on_create_media_trigger:
            event.listen(models.Media, "after_insert", TriggerMediaCaller(trigger))

    def _get_alembic_config(self):
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", "metrico.database:migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", self.config.url)
        return alembic_cfg

    def _get_session(self, session: Session | None = None):
        if session is None:
            return self.Session()
        return session

    def reload_config(self):
        self.engine = create_engine(self.config.db.url, echo=self.config.db.enable_echo)
        self.Session = sessionmaker(autoflush=True, bind=self.engine)  # pylint: disable=invalid-name
        return self.engine, self.Session

    def setup(self):
        models.Base.metadata.create_all(self.engine)

    def make_migrations(self, message: str | None = None):
        alembic_cfg = self._get_alembic_config()
        with self.engine.begin() as connection:
            alembic_cfg.attributes["connection"] = connection
            command.revision(alembic_cfg, message=message, autogenerate=True)

    def migrate(self):
        with self.engine.begin() as connection:
            alembic_cfg = self._get_alembic_config()
            alembic_cfg.attributes["connection"] = connection
            command.upgrade(alembic_cfg, "head")

    def stats(self, model: str | None = None):
        alchemy_map = {
            "Account": models.Account,
            "Account-Subscription": models.AccountSubscription,
            "Account-Info": models.AccountInfo,
            "Account-Data": models.AccountStats,
            "Media": models.Media,
            "Media-Info": models.MediaInfo,
            "Media-Data": models.MediaStats,
            "Media-Comment": models.MediaComment,
        }
        with self.Session() as session:
            if model in alchemy_map:
                return session.query(alchemy_map[model]).count()
            return {name: session.query(model).count() for name, model in alchemy_map.items()}

    def iter_query(self, stmt: BasicQuery):
        with self.Session() as session:
            yield from stmt.iter(session)

    def count_query(self, stmt: BasicQuery):
        with self.Session() as session:
            sub_stmt = stmt.query()
            count_stmt = select(func.count()).select_from(sub_stmt.subquery())
            return session.scalar(count_stmt)

    def create(self, platform: str, data: schemas.Account | schemas.Media, session: Session | None = None):
        match data:
            case schemas.Account():
                return self.create_account(platform, data, session)
            case schemas.Media():
                return self.create_media(platform, data, session)

    def create_account(self, platform: str, data: schemas.Account, session: Session | None = None):
        if session is not None:
            return crud.create_account(session, platform, data)

        with self.Session() as local_session:
            account = crud.create_account(local_session, platform, data)
            local_session.commit()
            local_session.refresh(account)
            return account

    def create_media(self, platform: str, data: schemas.Media, session: Session | None = None):
        if session is not None:
            account = crud.create_account(session, platform, data.account)
            return crud.create_media(session, account, data)

        with self.Session() as local_session:
            account = crud.create_account(local_session, platform, data.account)
            media = crud.create_media(local_session, account, data)
            local_session.commit()
            local_session.refresh(media)
            return media

    def get_account(self, account_id: int | str, session: Session | None = None):
        if session is not None:
            return crud.get_account(session, account_id=account_id)
        with self.Session() as local_session:
            return crud.get_account(local_session, account_id=account_id)

    def get_media(self, media_id: int, session: Session | None = None):
        if session is not None:
            return crud.get_media(session, media_id=media_id)
        with self.Session() as local_session:
            return crud.get_media(local_session, media_id=media_id)

    def get_trigger(self, trigger: str | int, session: Session | None = None):
        if session is not None:
            return crud.get_trigger(session, trigger)
        with self.Session() as local_session:
            return crud.get_trigger(local_session, trigger)

    def add_accounts_to_trigger(self, trigger_name: str, accounts: list[int], session: Session | None = None):
        with self._get_session(session) as local_session:
            trigger = crud.get_trigger(local_session, trigger=trigger_name)

            for account_id in accounts:
                if account := crud.get_account(local_session, account_id=account_id):
                    crud.add_to_trigger(local_session, trigger=trigger, account=account)
            local_session.commit()
