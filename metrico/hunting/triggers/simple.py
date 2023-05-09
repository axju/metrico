from __future__ import annotations

from typing import TYPE_CHECKING

from logging import getLogger

from sqlalchemy.sql import func

from metrico.database import crud
from metrico.database.models import TriggerAccount, TriggerMedia
from metrico.utils.misc import update_list

from .basic import BasicTrigger

if TYPE_CHECKING:
    from metrico.core import MetricoCore

logger = getLogger(__name__)


class SimpleTrigger(BasicTrigger):
    def get_list_query(self, trigger):
        account_query, media_query = trigger.accounts, trigger.medias

        match self.config.get("order"):
            case "random":
                account_query, media_query = account_query.order_by(func.random()), media_query.order_by(func.random())
            case "desc":
                account_query, media_query = account_query.order_by(TriggerAccount.timestamp.desc()), media_query.order_by(TriggerMedia.timestamp.desc())
            case "asc" | _:
                account_query, media_query = account_query.order_by(TriggerAccount.timestamp.asc()), media_query.order_by(TriggerMedia.timestamp.asc())

        if limit := self.config.get("limit", 100):
            account_query, media_query = account_query.limit(limit), media_query.limit(limit)
        return account_query, media_query

    def trigger_action(self, metrico: MetricoCore, account_ids: list[int], media_ids: list[int]) -> bool:
        if account_ids:
            update_list(
                ids=account_ids,
                func=metrico.update_account,
                threads=self.config.get("threads", 4),
                media_count=self.config.get("media_count", -1),
                comment_count=self.config.get("comment_count", -1),
                subscription_count=self.config.get("subscription_count", -1),
            )
        if media_ids:
            update_list(
                ids=media_ids,
                func=metrico.update_media,
                threads=self.config.get("threads", 4),
                comment_count=self.config.get("comment_count", -1),
            )

        if self.config.get("single_call", False):
            with metrico.db.Session() as local_session:
                for account_id in account_ids:
                    crud.remove_from_trigger(local_session, trigger=self.name, account=account_id)
                for media_id in media_ids:
                    crud.remove_from_trigger(local_session, trigger=self.name, media=media_id)
                local_session.commit()
        return True
