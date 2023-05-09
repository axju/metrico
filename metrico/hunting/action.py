from __future__ import annotations

from typing import TYPE_CHECKING

from logging import getLogger

from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from metrico import schemas
from metrico.database import crud, models

if TYPE_CHECKING:
    from metrico.core import MetricoHunters


logger = getLogger(__name__)


def update_account(
    session: Session,
    account: models.Account,
    hunter: MetricoHunters | None = None,
    media_count: int = 0,
    comment_count: int = -2,
    subscription_count: int = -1,
    data: schemas.Account | None = None,
):
    """
    update an account with data

    :param session: just the database session
    :param account: the selected account
    :param hunter: a MetricoCore object
    :param media_count: -2 -> skipp if nothing to to, -1 -> skipp account medias, 0 -> update alle medias, n -> only the last n medias
    :param comment_count: -2 -> skipp if nothing to to, -1 -> skipp media comments, 0 -> update media comments, n -> only the last n comments
    :param subscription_count: -2 -> skipp if nothing to to, -1 -> skipp subscription, 0 -> update subscription, n -> only the last n subscription
    :param data: set the data for the account, if None load the data from the account platform
    """
    if data is None and hunter is not None:
        data = hunter[account.platform].get_account_data(account.identifier)

    if data is None:
        logger.warning("account:%8i - no data -> exit", account.id)
        account.status = schemas.ModelStatus.FAIL
        # session.commit()
        return

    logger.info("account:%8i - update start ", account.id)
    crud.update_account(session, account, data.info, data.stats)

    if hunter is None:
        logger.warning("account:%08i - no Hunter to get media or subscriptions data -> exit")
        return

    if media_count == -2 and data.stats and data.stats.medias != account.medias.count():  # type: ignore
        media_count = data.stats.medias - account.medias.count() if data.stats.medias else 0  # type: ignore
    update_account_medias(session, hunter, account, media_count, comment_count)

    if subscription_count == -2 and data.stats and data.stats.subscriptions != account.subscriptions.count():  # type: ignore
        subscription_count = 0
    update_account_subscriptions(session, hunter, account, subscription_count)
    logger.info("account:%8i - update finished ", account.id)


def update_account_medias(
    session: Session,
    hunter: MetricoHunters,
    account: models.Account,
    media_count: int = 0,
    comment_count: int = -1,
):
    # account.medias_last_update = func.now()
    # session.commit()

    if media_count < 0:
        logger.debug("account:%8i - update medias skipped ", account.id)
        return

    logger.info("account:%8i - update medias finished ", account.id)
    for item in hunter[account.platform].iter_account_media(account.identifier, amount=media_count):
        media = crud.create_media(session, account, item)
        if media is None:
            logger.warning("account:%8i - no media ", account.id)
            continue
        update_media(session, hunter, media, comment_count, item)
    logger.info("account:%8i - update medias finished ", account.id)


def update_account_subscriptions(
    session: Session,
    hunter: MetricoHunters,
    account: models.Account,
    subscription_count: int = 0,
):
    account.subscriptions_last_update = func.now()
    # session.commit()

    if subscription_count < 0:
        logger.debug("account:%8i - update subscriptions skipped ", account.id)
        return

    logger.info("account:%8i - update subscriptions start ", account.id)
    for subscription in hunter[account.platform].iter_account_subscriptions(account.identifier, amount=subscription_count):
        crud.update_account(session, account, subscription)
    logger.info("account:%8i - update subscriptions finished ", account.id)


def update_media(
    session: Session,
    hunter: MetricoHunters,
    media: models.Media,
    comment_count: int = -2,
    data: schemas.Media | None = None,
):
    if data is None:
        if hunter is None:
            raise Exception("No hunters and no data!")
        data = hunter[media.account.platform].get_media_data(media.identifier)

    if data is None:
        logger.warning("media:%8i - no data -> exit", media.id)
        media.status = schemas.ModelStatus.FAIL
        # session.commit()
        return

    logger.info("media:%8i - update start", media.id)
    crud.update_media(session, media, data.created, data.info, data.stats)
    if data.info and data.info.disable_comments:
        comment_count = -1
    if comment_count == -2 and data.stats and data.stats.comments != media.comments.count():  # type: ignore
        comment_count = 0
    update_media_comments(session, media, hunter, comment_count)
    logger.info("media:%8i - update finished", media.id)


def update_media_comments(session: Session, media: models.Media, hunter: MetricoHunters, comment_count: int = -1):
    media.comments_last_update = func.now()
    # session.commit()

    if comment_count < 0:
        logger.debug("media:%8i - update comments skipped ", media.id)
        return

    logger.info("media:%8i - update comments start ", media.id)
    for comment in hunter[media.account.platform].iter_media_comments(media.identifier, amount=comment_count):
        crud.update_media(session, media, comment)
    logger.info("media:%8i - update comments finished ", media.id)
