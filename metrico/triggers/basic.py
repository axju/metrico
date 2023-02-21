from __future__ import annotations

from typing import TYPE_CHECKING

from datetime import datetime
from logging import getLogger

from metrico.database import crud
from metrico.database.alchemy import TriggerAccount, TriggerMedia
from metrico.models import BasicClassItem, TriggerStatus

if TYPE_CHECKING:
    from metrico import MetricoCore


logger = getLogger(__name__)


class BasicTrigger(BasicClassItem):
    def __init__(self, name: str, config: dict):
        super().__init__(config)
        self.name: str = name

    def get_list(self, trigger):
        account_query, media_query = self.get_list_query(trigger)
        return [obj.id for obj in account_query], [obj.id for obj in media_query]

    def get_list_query(self, trigger):
        return trigger.accounts.order_by(TriggerAccount.timestamp.asc()), trigger.medias.order_by(TriggerMedia.timestamp.asc())

    def trigger_action(self, metrico: MetricoCore, account_ids: list[int], media_ids: list[int]) -> bool:
        logger.debug("trigger_action metrico=%s, len(account_ids)=%s, len(media_ids)=%s", metrico, len(account_ids), len(media_ids))
        return False

    def run(self, metrico: MetricoCore, **config) -> None:
        self.config.update(config)
        with metrico.db.Session() as session:
            trigger = metrico.db.get_trigger(trigger=self.name, session=session)
            account_ids, media_ids = self.get_list(trigger)
            trigger.status = TriggerStatus.RUN
            session.commit()

        success, started = False, datetime.now()
        logger.info("start triggers at %s with %i accounts and %i medias", started, len(account_ids), len(media_ids))
        try:
            success = self.trigger_action(metrico, account_ids, media_ids)
        except KeyboardInterrupt:
            logger.info("Break update triggers")
        except:
            logger.exception("Fail to run update triggers")

        with metrico.db.Session() as local_session:
            crud.add_trigger_stats(local_session, trigger=self.name, success=success, started=started, finished=datetime.now())
            local_session.commit()
