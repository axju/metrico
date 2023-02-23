"""
CRUD comes from: Create, Read, Update, and Delete.

No session.commit !!!
"""
from dataclasses import asdict
from datetime import datetime
from logging import getLogger

from sqlalchemy import delete
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from metrico import models
from metrico.database import alchemy

logger = getLogger(__name__)


def create_obj(session: Session, model, **data):
    created_obj = model(**data)
    session.add(created_obj)
    session.flush()
    logger.debug("create: %s", created_obj)
    return created_obj


def get_or_create(session: Session, model, filter_by: dict, fields: dict | None = None, update_fields: bool = False):
    obj = session.query(model).filter_by(**filter_by).order_by(model.timestamp.desc()).first()
    if obj is None:
        kwargs = dict(filter_by)
        if isinstance(fields, dict):
            kwargs.update(fields)
        return create_obj(session, model, **kwargs)

    if fields is None:
        return obj

    for field, value in fields.items():
        if value is None or getattr(obj, field) == value:
            continue

        if not update_fields:
            return create_obj(session, model, **filter_by, **fields)

        setattr(obj, field, value)

    return obj


def add_rel_data(session: Session, obj_name, obj, name, model, fields):
    add_obj = False
    for field, value in fields.items():
        if value is None:
            fields[field] = getattr(obj, f"{name}_{field}")
            continue
        if getattr(obj, f"{name}_{field}") != value:
            setattr(obj, f"{name}_{field}", value)
            add_obj = True
    setattr(obj, f"{name}_last_update", func.now())

    if add_obj:
        create_obj(session, model, **{obj_name: obj}, **fields)


def create_account(session: Session, platform: str, data: models.Account | None, update: bool = True):
    if data is None:
        return None
    account = get_or_create(session, alchemy.Account, filter_by={"platform": platform, "identifier": data.identifier})
    if update:
        update_account(session, account, data)
    return account


def create_media(session: Session, account: alchemy.Account, data: models.Media, update: bool = True):
    media = get_or_create(
        session,
        alchemy.Media,
        filter_by={
            "account": account,
            "identifier": data.identifier,
            "media_type": data.media_type,
        },
    )
    if update:
        update_media(session, media, data)
    return media


def get_account(session: Session, account_id: int | str) -> alchemy.Account | None:
    if isinstance(account_id, str):
        return session.query(alchemy.Account).filter_by(info_name=account_id).one_or_none()
    return session.query(alchemy.Account).filter_by(id=account_id).one_or_none()


def update_account(
    session: Session,
    account: alchemy.Account,
    *args: models.Account | models.Created | models.AccountInfo | models.AccountStats | models.Subscription | None,
):
    for arg in args:
        match arg:
            case models.Account():
                update_account(session, account, arg.created, arg.info, arg.stats)

            case models.Created():
                if arg.value:
                    account.created_at = arg.value

            case models.AccountInfo():
                add_rel_data(session, "account", account, "info", alchemy.AccountInfo, asdict(arg))

            case models.AccountStats():
                add_rel_data(session, "account", account, "stats", alchemy.AccountStats, asdict(arg))

            case models.Subscription():
                subscribed_account = create_account(session, account.platform, arg.account)
                get_or_create(session, alchemy.AccountSubscription, filter_by={"account": account, "subscribed_account": subscribed_account})

            case None:
                pass
            case _:
                logger.warning("Objects of type %s can not be updated with the account model", type(arg))


def get_media(session: Session, media_id: int | str):
    return session.query(alchemy.Media).filter_by(id=media_id).one_or_none()


def update_media(
    session: Session, media: alchemy.Media, *args: models.Media | models.Created | models.MediaInfo | models.MediaStats | models.MediaComment | None
):
    for arg in args:
        match arg:
            case models.Media():
                update_media(session, media, arg.created, arg.info, arg.stats)

            case models.Created():
                if arg.value:
                    media.created_at = arg.value

            case models.MediaInfo():
                add_rel_data(session, "media", media, "info", alchemy.MediaInfo, asdict(arg))

            case models.MediaStats():
                add_rel_data(session, "media", media, "stats", alchemy.MediaStats, asdict(arg))

            case models.MediaComment():
                fields = asdict(arg.content)
                fields["account"] = create_account(session, media.account.platform, arg.account) if arg.account else None
                get_or_create(
                    session,
                    alchemy.MediaComment,
                    filter_by={"media": media, "identifier": arg.identifier},
                    fields=fields,
                    update_fields=True,
                )

            case None:
                pass
            case _:
                logger.warning("Objects of type %s can not be updated with the media model", type(arg))


def get_trigger_id(session: Session, trigger: alchemy.Trigger | str | int):
    match trigger:
        case str():
            obj = get_trigger(session, trigger)
            return obj.id
        case alchemy.Trigger():
            return trigger.id
        case _:
            return trigger


def get_trigger(session: Session, trigger: str | int):
    if isinstance(trigger, str):
        trigger = get_or_create(session, alchemy.Trigger, filter_by={"name": trigger})
        # if isinstance(trigger, alchemy.Trigger) and trigger.id is None:
        #     session.commit()
        return trigger
    return session.query(alchemy.Trigger).filter_by(id=trigger).one_or_none()


def add_trigger_stats(
    session: Session,
    trigger: alchemy.Trigger | str | int,
    success: bool,
    started: datetime,
    finished: datetime,
):
    if isinstance(trigger, (str, int)):
        obj = get_trigger(session, trigger)
    else:
        obj = trigger

    obj.status = models.TriggerStatus.WAIT if success else models.TriggerStatus.ERROR
    get_or_create(
        session,
        alchemy.TriggerStats,
        filter_by={
            "trigger_id": obj.id,
        },
        fields={"success": success, "started": started, "finished": finished},
    )


def add_to_trigger(
    session: Session,
    trigger: alchemy.Trigger | str | int,
    account: int | alchemy.Account | None = None,
    media: int | alchemy.Media | None = None,
):
    trigger_id = get_trigger_id(session, trigger)

    match account:
        case int():
            get_or_create(session, alchemy.TriggerAccount, filter_by={"trigger_id": trigger_id, "account_id": account})
        case alchemy.Account():
            get_or_create(session, alchemy.TriggerAccount, filter_by={"trigger_id": trigger_id, "account_id": account.id})

    match media:
        case int():
            get_or_create(session, alchemy.TriggerMedia, filter_by={"trigger_id": trigger_id, "media_id": media})
        case alchemy.Account():
            get_or_create(session, alchemy.TriggerMedia, filter_by={"trigger_id": trigger_id, "media_id": media.id})


def remove_from_trigger(
    session: Session,
    trigger: alchemy.Trigger | str | int,
    account: int | alchemy.Account | None = None,
    media: int | alchemy.Media | None = None,
):
    trigger_id = get_trigger_id(session, trigger)

    stmt = None
    match account:
        case int():
            stmt = delete(alchemy.TriggerAccount).where(alchemy.TriggerAccount.trigger_id == trigger_id, alchemy.TriggerAccount.account_id == account)
        case alchemy.Account():
            stmt = delete(alchemy.TriggerAccount).where(alchemy.TriggerAccount.trigger_id == trigger_id, alchemy.TriggerAccount.account_id == account.id)
    match media:
        case int():
            stmt = delete(alchemy.TriggerMedia).where(alchemy.TriggerMedia.trigger_id == trigger_id, alchemy.TriggerMedia.media_id == media)
        case alchemy.Account():
            stmt = delete(alchemy.TriggerMedia).where(alchemy.TriggerMedia.trigger_id == trigger_id, alchemy.TriggerMedia.media_id == media.id)

    if stmt is not None:
        session.execute(stmt)
    # if commit:
    #     session.commit()
