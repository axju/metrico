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

from metrico import schemas
from metrico.database import models

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


def create_account(session: Session, platform: str, data: schemas.Account | None, update: bool = True):
    if data is None:
        return None
    account = get_or_create(session, models.Account, filter_by={"platform": platform, "identifier": data.identifier})
    if update:
        update_account(session, account, data)
    return account


def create_media(session: Session, account: models.Account, data: schemas.Media, update: bool = True):
    media = get_or_create(
        session,
        models.Media,
        filter_by={
            "account": account,
            "identifier": data.identifier,
            "media_type": data.media_type,
        },
    )
    if update:
        update_media(session, media, data)
    return media


def get_account(session: Session, account_id: int | str) -> models.Account | None:
    if isinstance(account_id, str):
        return session.query(models.Account).filter_by(info_name=account_id).one_or_none()
    return session.query(models.Account).filter_by(id=account_id).one_or_none()


def update_account(
    session: Session,
    account: models.Account,
    *args: schemas.Account | schemas.Created | schemas.AccountInfo | schemas.AccountStats | schemas.Subscription | None,
):
    for arg in args:
        match arg:
            case schemas.Account():
                update_account(session, account, arg.created, arg.info, arg.stats)

            case schemas.Created():
                if arg.value:
                    account.created_at = arg.value

            case schemas.AccountInfo():
                add_rel_data(session, "account", account, "info", models.AccountInfo, asdict(arg))

            case schemas.AccountStats():
                add_rel_data(session, "account", account, "stats", models.AccountStats, asdict(arg))

            case schemas.Subscription():
                subscribed_account = create_account(session, account.platform, arg.account)
                get_or_create(session, models.AccountSubscription, filter_by={"account": account, "subscribed_account": subscribed_account})

            case None:
                pass
            case _:
                logger.warning("Objects of type %s can not be updated with the account model", type(arg))


def get_media(session: Session, media_id: int | str):
    return session.query(models.Media).filter_by(id=media_id).one_or_none()


def update_media(
    session: Session, media: models.Media, *args: schemas.Media | schemas.Created | schemas.MediaInfo | schemas.MediaStats | schemas.MediaComment | None
):
    for arg in args:
        match arg:
            case schemas.Media():
                update_media(session, media, arg.created, arg.info, arg.stats)

            case schemas.Created():
                if arg.value:
                    media.created_at = arg.value

            case schemas.MediaInfo():
                add_rel_data(session, "media", media, "info", models.MediaInfo, asdict(arg))

            case schemas.MediaStats():
                add_rel_data(session, "media", media, "stats", models.MediaStats, asdict(arg))

            case schemas.MediaComment():
                fields = asdict(arg.content)
                fields["account"] = create_account(session, media.account.platform, arg.account) if arg.account else None
                get_or_create(
                    session,
                    models.MediaComment,
                    filter_by={"media": media, "identifier": arg.identifier},
                    fields=fields,
                    update_fields=True,
                )

            case None:
                pass
            case _:
                logger.warning("Objects of type %s can not be updated with the media model", type(arg))


def get_trigger_id(session: Session, trigger: models.Trigger | str | int):
    match trigger:
        case str():
            obj = get_trigger(session, trigger)
            return obj.id
        case models.Trigger():
            return trigger.id
        case _:
            return trigger


def get_trigger(session: Session, trigger: str | int):
    if isinstance(trigger, str):
        trigger = get_or_create(session, models.Trigger, filter_by={"name": trigger})
        # if isinstance(trigger, models.Trigger) and trigger.id is None:
        #     session.commit()
        return trigger
    return session.query(models.Trigger).filter_by(id=trigger).one_or_none()


def add_trigger_stats(
    session: Session,
    trigger: models.Trigger | str | int,
    success: bool,
    started: datetime,
    finished: datetime,
):
    if isinstance(trigger, (str, int)):
        obj = get_trigger(session, trigger)
    else:
        obj = trigger

    obj.status = schemas.TriggerStatus.WAIT if success else schemas.TriggerStatus.ERROR
    get_or_create(
        session,
        models.TriggerStats,
        filter_by={
            "trigger_id": obj.id,
        },
        fields={"success": success, "started": started, "finished": finished},
    )


def add_to_trigger(
    session: Session,
    trigger: models.Trigger | str | int,
    account: int | models.Account | None = None,
    media: int | models.Media | None = None,
):
    trigger_id = get_trigger_id(session, trigger)

    match account:
        case int():
            get_or_create(session, models.TriggerAccount, filter_by={"trigger_id": trigger_id, "account_id": account})
        case models.Account():
            get_or_create(session, models.TriggerAccount, filter_by={"trigger_id": trigger_id, "account_id": account.id})

    match media:
        case int():
            get_or_create(session, models.TriggerMedia, filter_by={"trigger_id": trigger_id, "media_id": media})
        case models.Account():
            get_or_create(session, models.TriggerMedia, filter_by={"trigger_id": trigger_id, "media_id": media.id})


def remove_from_trigger(
    session: Session,
    trigger: models.Trigger | str | int,
    account: int | models.Account | None = None,
    media: int | models.Media | None = None,
):
    trigger_id = get_trigger_id(session, trigger)

    stmt = None
    match account:
        case int():
            stmt = delete(models.TriggerAccount).where(models.TriggerAccount.trigger_id == trigger_id, models.TriggerAccount.account_id == account)
        case models.Account():
            stmt = delete(models.TriggerAccount).where(models.TriggerAccount.trigger_id == trigger_id, models.TriggerAccount.account_id == account.id)
    match media:
        case int():
            stmt = delete(models.TriggerMedia).where(models.TriggerMedia.trigger_id == trigger_id, models.TriggerMedia.media_id == media)
        case models.Account():
            stmt = delete(models.TriggerMedia).where(models.TriggerMedia.trigger_id == trigger_id, models.TriggerMedia.media_id == media.id)

    if stmt is not None:
        session.execute(stmt)
    # if commit:
    #     session.commit()
