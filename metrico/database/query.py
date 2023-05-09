from typing import Any

from argparse import Namespace
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from logging import getLogger

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute, Session
from sqlalchemy.sql import Select, func

from metrico.database.models import Account, Base, Media, MediaComment
from metrico.schemas import ModelStatus

logger = getLogger(__name__)


class IterMode(Enum):
    SCALAR = 0
    SCALARS = 1
    ALL = 2


class AccountOrder(Enum):
    CREATED = 0
    UPDATED = 1
    COMMENTS = 2
    MEDIAS = 3
    VIEWS = 4
    FOLLOWERS = 5
    SUBSCRIPTIONS = 6
    RANDOM = 7

    def __str__(self):
        return self.name


class MediaOrder(Enum):
    CREATED = 0
    UPDATED = 1
    COMMENTS = 2
    LIKES = 3
    VIEWS = 4
    RANDOM = 5

    def __str__(self):
        return self.name


class MediaCommentOrder(Enum):
    CREATED = 0
    TIMESTAMP = 1
    LIKES = 2
    RANDOM = 3

    def __str__(self):
        return self.name


@dataclass
class BasicQuery:
    model: type[Account] | type[Media] | type[MediaComment] | type[Base] = Base
    limit: int = 0
    offset: int = 0
    created: tuple[datetime, datetime] | None = None
    status: ModelStatus | None = None
    accounts: str | int | list[str] | list[int] | None = None

    @classmethod
    def from_namespace(cls, args: Namespace):
        obj = cls()
        obj.load_namespace(args)
        return obj

    def load_namespace(self, args: Namespace):
        self.limit = args.limit
        self.offset = args.offset
        self.created = args.filter_datetime
        self.status = args.filter_status
        self.accounts = args.filter_account_id or args.filter_account

    def query(self, stmt: Select[Any] | None = None) -> Select[Any]:
        if stmt is None:
            stmt = select(self.model)
        stmt = self.query_limit_offset(stmt)
        stmt = self.query_filter_created(stmt)
        stmt = self.query_filter_status(stmt)
        return stmt

    def query_limit_offset(self, stmt: Select[Any]) -> Select[Any]:
        if self.offset:
            stmt = stmt.offset(self.offset)
        if self.limit:
            stmt = stmt.limit(self.limit)
        return stmt

    def query_filter_created(self, stmt: Select[Any]) -> Select[Any]:
        if self.created:
            stmt = stmt.where(self.model.created_at.between(*self.created))  # type: ignore
        return stmt

    def query_filter_status(self, stmt: Select[Any]) -> Select[Any]:
        match self.status:
            case ModelStatus.OKAY:
                return stmt.where(self.model.status == ModelStatus.OKAY)  # type: ignore
            case ModelStatus.FAIL:
                return stmt.where(self.model.status == ModelStatus.FAIL)  # type: ignore
        return stmt

    def iter(self, session: Session):
        stmt = self.query()
        result = session.execute(stmt)
        yield from result.scalars()


@dataclass
class AccountQuery(BasicQuery):
    model: type[Account] = Account
    order_by: AccountOrder = AccountOrder.CREATED
    order_asc: bool = False
    medias: int | list[int] | None = None
    stats_null: bool = False
    stats_views_null: bool = False

    def load_namespace(self, args: Namespace):
        super().load_namespace(args)
        self.order_by = args.order_by
        self.order_asc = args.order_asc
        self.medias = args.filter_comment_media_id
        self.stats_null = args.filter_stats_null
        self.stats_views_null = args.filter_stats_views_null

    def query(self, stmt: Select[Any] | None = None) -> Select[Any]:
        if self.medias:
            stmt = select(Account).join(MediaComment, MediaComment.account_id == Account.id)
        stmt = super().query(stmt)
        stmt = self.query_order(stmt)
        stmt = self.query_filter_account(stmt)
        stmt = self.query_filter_comment_media(stmt)
        stmt = self.query_filter_stats(stmt)
        stmt = stmt.group_by(Account.id)
        return stmt

    def query_order(self, stmt: Select[Any]) -> Select[Any]:
        order_field: InstrumentedAttribute[Any]
        match self.order_by:
            case AccountOrder.CREATED:
                order_field = Account.created_at
            case AccountOrder.UPDATED:
                order_field = Account.stats_last_update
            case AccountOrder.COMMENTS:
                if self.order_asc:
                    return stmt.order_by(func.count(MediaComment.id))
                return stmt.order_by(func.count(MediaComment.id).desc())
            case AccountOrder.MEDIAS:
                order_field = Account.stats_medias
            case AccountOrder.VIEWS:
                order_field = Account.stats_views
            case AccountOrder.FOLLOWERS:
                order_field = Account.stats_followers
            case AccountOrder.SUBSCRIPTIONS:
                order_field = Account.stats_subscriptions
            case AccountOrder.RANDOM:
                return stmt.order_by(func.random())
            case _:
                order_field = Account.id
        if self.order_asc:
            return stmt.order_by(order_field.nulls_last())
        return stmt.order_by(order_field.desc().nulls_last())

    def query_filter_account(self, stmt: Select[Any]) -> Select[Any]:
        if isinstance(self.accounts, list) and len(self.accounts) == 1:
            self.accounts = self.accounts[0]
        if isinstance(self.accounts, str):
            return stmt.where(Account.info_name == self.accounts)
        if isinstance(self.accounts, int):
            return stmt.where(Account.id == self.accounts)
        if isinstance(self.accounts, list):
            if all(isinstance(item, str) for item in self.accounts):
                return stmt.where(Account.info_name.in_(self.accounts))
            if all(isinstance(item, int) for item in self.accounts):
                return stmt.where(Account.id.in_(self.accounts))
        return stmt

    def query_filter_comment_media(self, stmt: Select[Any]) -> Select[Any]:
        if isinstance(self.medias, list) and len(self.medias) == 1:
            self.medias = self.medias[0]
        if isinstance(self.medias, int):
            return stmt.where(MediaComment.media_id == self.medias)
        if isinstance(self.medias, list) and all(isinstance(item, int) for item in self.medias):
            return stmt.where(MediaComment.media_id.in_(self.medias))
        return stmt

    def query_filter_stats(self, stmt: Select[Any]) -> Select[Any]:
        if self.stats_null:
            stmt = stmt.where(~Account.stats.any())
        if self.stats_views_null:
            stmt = stmt.where(Account.stats_views.is_(None))
        return stmt


@dataclass
class MediaQuery(BasicQuery):
    model: type[Media] = Media
    order_by: MediaOrder = MediaOrder.CREATED
    order_asc: bool = False

    def load_namespace(self, args: Namespace):
        super().load_namespace(args)
        self.order_by = args.order_by
        self.order_asc = args.order_asc

    def query(self, stmt: Select[Any] | None = None) -> Select[Any]:
        stmt = super().query(stmt)
        stmt = self.query_order(stmt)
        stmt = self.query_filter_account(stmt)
        return stmt

    def query_order(self, stmt: Select[Any]) -> Select[Any]:
        order_field: InstrumentedAttribute[Any]
        match self.order_by:
            case MediaOrder.CREATED:
                order_field = Media.created_at
            case MediaOrder.COMMENTS:
                order_field = Media.stats_comments
            case MediaOrder.LIKES:
                order_field = Media.stats_likes
            case MediaOrder.VIEWS:
                order_field = Media.stats_views
            case MediaOrder.RANDOM:
                return stmt.order_by(func.random())
            case _:
                order_field = Media.id
        if self.order_asc:
            return stmt.order_by(order_field)
        return stmt.order_by(order_field.desc())

    def query_filter_account(self, stmt: Select[Any]) -> Select[Any]:
        if isinstance(self.accounts, list) and len(self.accounts) == 1:
            self.accounts = self.accounts[0]
        if isinstance(self.accounts, str):
            return stmt.join(Account, Media.account_id == Account.id).where(Account.info_name.contains(self.accounts))
        if isinstance(self.accounts, int):
            return stmt.where(Media.account_id == self.accounts)
        if isinstance(self.accounts, list):
            if all(isinstance(item, str) for item in self.accounts):
                return stmt.join(Account, Media.account_id == Account.id).where(Account.info_name.in_(self.accounts))
            if all(isinstance(item, int) for item in self.accounts):
                return stmt.where(Media.account_id.in_(self.accounts))
        return stmt


@dataclass
class MediaCommentQuery(BasicQuery):
    model: type[MediaComment] = MediaComment
    order_by: MediaCommentOrder = MediaCommentOrder.CREATED
    order_asc: bool = False
    media_account_id: int | list[int] | None = None

    def load_namespace(self, args: Namespace):
        super().load_namespace(args)
        self.order_by = args.order_by
        self.order_asc = args.order_asc

    def query(self, stmt: Select[Any] | None = None) -> Select[Any]:
        stmt = super().query(stmt)
        stmt = self.query_order(stmt)
        stmt = self.query_filter_account(stmt)
        stmt = self.query_filter_media_account(stmt)
        return stmt

    def query_order(self, stmt: Select[Any]) -> Select[Any]:
        order_field: InstrumentedAttribute[Any]
        match self.order_by:
            case MediaCommentOrder.CREATED:
                order_field = MediaComment.created_at
            case MediaCommentOrder.TIMESTAMP:
                order_field = MediaComment.timestamp
            case MediaCommentOrder.LIKES:
                order_field = MediaComment.likes
            case MediaOrder.RANDOM:
                return stmt.order_by(func.random())
            case _:
                order_field = MediaComment.id
        if self.order_asc:
            return stmt.order_by(order_field)
        return stmt.order_by(order_field.desc())

    def query_filter_account(self, stmt: Select[Any]) -> Select[Any]:
        if isinstance(self.accounts, list) and len(self.accounts) == 1:
            self.accounts = self.accounts[0]
        if isinstance(self.accounts, str):
            return stmt.join(Account, MediaComment.account_id == Account.id).where(Account.info_name.contains(self.accounts))
        if isinstance(self.accounts, int):
            return stmt.where(MediaComment.account_id == self.accounts)
        if isinstance(self.accounts, list):
            if all(isinstance(item, str) for item in self.accounts):
                return stmt.join(Account, MediaComment.account_id == Account.id).where(Account.info_name.in_(self.accounts))
            if all(isinstance(item, int) for item in self.accounts):
                return stmt.where(MediaComment.account_id.in_(self.accounts))
        return stmt

    def query_filter_media_account(self, stmt: Select[Any]) -> Select[Any]:
        if isinstance(self.media_account_id, list) and len(self.media_account_id) == 1:
            self.media_account_id = self.media_account_id[0]
        if isinstance(self.media_account_id, int):
            return stmt.join(Media, Media.id == MediaComment.media_id).where(Media.account_id == self.media_account_id)
        return stmt


# def call_result(result: Result[Any], mode: IterMode = IterMode.SCALARS):
#     match mode:
#         case IterMode.SCALAR:
#             return result.scalar()
#         case IterMode.SCALARS:
#             yield from result.scalars()
#         case IterMode.ALL:
#             yield from result.all()
#         case _:
#             yield from result.scalars()
#
#
# def query_limit_offset(stmt: Select[Any], limit: int = 0, offset: int = 0):
#     if offset:
#         stmt = stmt.offset(offset)
#     if limit:
#         stmt = stmt.limit(limit)
#     return stmt
#
#
# def query_order_account(
#     stmt: Select[Any],
#     order_by: AccountOrder = AccountOrder.CREATED,
#     order_asc: bool = False,
# ) -> Select[Any]:
#     order_field: InstrumentedAttribute[Any]
#
#     match order_by:
#         case AccountOrder.CREATED:
#             order_field = Account.created_at
#         case AccountOrder.UPDATED:
#             order_field = Account.stats_last_update
#         case AccountOrder.COMMENTS:
#             if order_asc:
#                 return stmt.order_by(func.count(MediaComment.id))
#             return stmt.order_by(func.count(MediaComment.id).desc())
#         case AccountOrder.MEDIAS:
#             order_field = Account.stats_medias
#         case AccountOrder.VIEWS:
#             order_field = Account.stats_views
#         case AccountOrder.FOLLOWERS:
#             order_field = Account.stats_followers
#         case AccountOrder.SUBSCRIPTIONS:
#             order_field = Account.stats_subscriptions
#         case AccountOrder.RANDOM:
#             return stmt.order_by(func.random())
#         case _:
#             order_field = Account.id
#     if order_asc:
#         return stmt.order_by(order_field.nulls_last())
#     return stmt.order_by(order_field.desc().nulls_last())
#
#
# def query_order_by_media(
#     stmt: Select[Any],
#     order_by: MediaOrder = MediaOrder.CREATED,
#     order_asc: bool = False,
# ) -> Select[Any]:
#     order_field: InstrumentedAttribute[Any]
#
#     match order_by:
#         case MediaOrder.CREATED:
#             order_field = Media.created_at
#         case MediaOrder.COMMENTS:
#             order_field = Media.stats_comments
#         case MediaOrder.LIKES:
#             order_field = Media.stats_likes
#         case MediaOrder.VIEWS:
#             order_field = Media.stats_views
#         case MediaOrder.RANDOM:
#             return stmt.order_by(func.random())
#         case _:
#             order_field = Media.id
#
#     if order_asc:
#         return stmt.order_by(order_field)
#     return stmt.order_by(order_field.desc())
#
#
# def query_order_media_comment(
#     stmt: Select[Any],
#     order_by: MediaCommentOrder = MediaCommentOrder.CREATED,
#     order_asc: bool = False,
# ) -> Select[Any]:
#     order_field: InstrumentedAttribute[Any]
#
#     match order_by:
#         case MediaCommentOrder.CREATED:
#             order_field = MediaComment.created_at
#         case MediaCommentOrder.TIMESTAMP:
#             order_field = MediaComment.timestamp
#         case MediaCommentOrder.LIKES:
#             order_field = MediaComment.likes
#         case MediaOrder.RANDOM:
#             return stmt.order_by(func.random())
#         case _:
#             order_field = MediaComment.id
#
#     if order_asc:
#         return stmt.order_by(order_field)
#     return stmt.order_by(order_field.desc())
#
#
# def query_filter_created(
#     stmt: Select[Any],
#     model: type[Account] | type[Media] | type[MediaComment],
#     created: tuple[datetime, datetime] | None = None,
# ):
#     if created:
#         return stmt.where(model.created_at.between(*created))  # type: ignore
#     return stmt
#
#
# def query_filter_comment_media(
#     stmt: Select[Any],
#     media: int | list[int] | None,
# ):
#     if isinstance(media, list) and len(media) == 1:
#         media = media[0]
#     if isinstance(media, int):
#         return stmt.where(MediaComment.media_id == media)
#     if isinstance(media, list) and all(isinstance(item, int) for item in media):
#         return stmt.where(MediaComment.media_id.in_(media))
#     return stmt
#
#
# def query_filter_comment_media_account(
#     stmt: Select[Any],
#     account: int | list[int] | None,
# ):
#     if isinstance(account, list) and len(account) == 1:
#         account = account[0]
#     if isinstance(account, int):
#         return stmt.join(Media, Media.id == MediaComment.media_id).where(Media.account_id == account)
#     return stmt
#
#
# def query_filter_account(
#     stmt: Select[Any],
#     model,  #: type[Account] | type[Media] | type[MediaComment],
#     accounts: str | int | list[str] | list[int] | None = None,
# ) -> Select[Any]:
#     if isinstance(accounts, list) and len(accounts) == 1:
#         accounts = accounts[0]
#     match model.__name__:
#         case "Account":
#             if isinstance(accounts, str):
#                 return stmt.where(Account.info_name == accounts)
#             if isinstance(accounts, int):
#                 return stmt.where(Account.id == accounts)
#
#             if isinstance(accounts, list):
#                 if all(isinstance(item, str) for item in accounts):
#                     return stmt.where(Account.info_name.in_(accounts))
#                 if all(isinstance(item, int) for item in accounts):
#                     return stmt.where(Account.id.in_(accounts))
#
#         case "Media" | "MediaComment":
#             if isinstance(accounts, str):
#                 return stmt.join(Account, model.account_id == Account.id).where(Account.info_name.contains(accounts))
#             if isinstance(accounts, int):
#                 return stmt.where(model.account_id == accounts)
#
#             if isinstance(accounts, list):
#                 if all(isinstance(item, str) for item in accounts):
#                     return stmt.join(Account, model.account_id == Account.id).where(Account.info_name.in_(accounts))
#                 if all(isinstance(item, int) for item in accounts):
#                     return stmt.where(model.account_id.in_(accounts))
#
#     return stmt
#
#
# def query_filter_media_accounts(stmt: Select[Any], accounts: int | list[int] | None = None):
#     if isinstance(accounts, int):
#         return stmt.join(Media, MediaComment.media_id == Media.id).where(Media.account_id == accounts)
#     if isinstance(accounts, list) and all(isinstance(item, int) for item in accounts):
#         return stmt.join(Media, MediaComment.media_id == Media.id).where(Media.account_id.in_(accounts))
#     return stmt
#
#
# def query_filter_stats(stmt: Select[Any], filter_stats_null: bool = False, filter_stats_views_null: bool = False):
#     if filter_stats_null:
#         stmt = stmt.where(~Account.stats.any())
#     if filter_stats_views_null:
#         stmt = stmt.where(Account.stats_views.is_(None))
#     return stmt
#
#
# def query_filter_status(stmt: Select[Any], model: type[Account] | type[Media] | type[MediaComment], filter_status: ModelStatus | None = None) -> Select[Any]:
#     match filter_status:
#         case ModelStatus.OKAY:
#             return stmt.where(model.status == ModelStatus.OKAY)  # type: ignore
#         case ModelStatus.FAIL:
#             return stmt.where(model.status == ModelStatus.FAIL)  # type: ignore
#     return stmt
#
#
# def query_account(
#     stmt: Select[Any],
#     limit: int = 0,
#     offset: int = 0,
#     order_by: AccountOrder = AccountOrder.CREATED,
#     order_asc: bool = False,
#     filter_status: ModelStatus | None = None,
#     filter_created: tuple[datetime, datetime] | None = None,
#     filter_account: str | int | list[str] | list[int] | None = None,
#     filter_stats_null: bool = False,
#     filter_stats_views_null: bool = False,
#     filter_comment_media_id: int | list[int] | None = None,
#     filter_comment_media_account_id: int | list[int] | None = None,
# ) -> Select[Any]:
#     stmt = query_order_account(stmt, order_by=order_by, order_asc=order_asc)
#     stmt = query_filter_account(stmt, model=Account, accounts=filter_account)
#     stmt = query_filter_created(stmt, model=Account, created=filter_created)
#     stmt = query_filter_status(stmt, model=Account, filter_status=filter_status)
#     stmt = query_filter_comment_media(stmt, filter_comment_media_id)
#     stmt = query_filter_comment_media_account(stmt, filter_comment_media_account_id)
#     stmt = query_filter_stats(stmt, filter_stats_null, filter_stats_views_null)
#     stmt = query_limit_offset(stmt, limit, offset)
#     return stmt
#
#
# def query_media(
#     limit: int = 0,
#     offset: int = 0,
#     order_by: MediaOrder = MediaOrder.CREATED,
#     order_asc: bool = False,
#     filter_created: tuple[datetime, datetime] | None = None,
#     filter_account: str | int | list[str] | list[int] | None = None,
# ):
#     stmt = select(Media)
#     stmt = query_filter_account(stmt, model=Media, accounts=filter_account)
#     stmt = query_filter_created(stmt, model=Media, created=filter_created)
#     stmt = query_order_by_media(stmt, order_by=order_by, order_asc=order_asc)
#     stmt = query_limit_offset(stmt, limit, offset)
#     return stmt
#
#
# def query_media_comments(
#     stmt: Select[Any],
#     limit: int = 0,
#     offset: int = 0,
#     order_by: MediaCommentOrder = MediaCommentOrder.CREATED,
#     order_asc: bool = False,
#     filter_created: tuple[datetime, datetime] | None = None,
#     filter_account: str | int | list[str] | list[int] | None = None,
#     filter_media_account: int | list[int] | None = None,
# ) -> Select[Any]:
#     stmt = query_filter_account(stmt, model=MediaComment, accounts=filter_account)
#     stmt = query_filter_media_accounts(stmt, filter_media_account)
#     stmt = query_filter_created(stmt, model=MediaComment, created=filter_created)
#     stmt = query_order_media_comment(stmt, order_by=order_by, order_asc=order_asc)
#     stmt = query_limit_offset(stmt, limit, offset)
#     return stmt
#
#
# def iter_accounts(
#     session: Session,
#     mode: IterMode = IterMode.SCALARS,
#     limit: int = 0,
#     offset: int = 0,
#     order_by: AccountOrder = AccountOrder.CREATED,
#     order_asc: bool = False,
#     filter_status: ModelStatus | None = None,
#     filter_created: tuple[datetime, datetime] | None = None,
#     filter_account: str | int | list[str] | list[int] | None = None,
#     filter_stats_null: bool = False,
#     filter_stats_views_null: bool = False,
#     filter_comment_media_id: int | list[int] | None = None,
#     filter_comment_media_account_id: int | list[int] | None = None,
# ):
#     stmt = select(Account)
#     stmt = query_account(
#         stmt,
#         limit=limit,
#         offset=offset,
#         order_by=order_by,
#         order_asc=order_asc,
#         filter_status=filter_status,
#         filter_created=filter_created,
#         filter_account=filter_account,
#         filter_stats_null=filter_stats_null,
#         filter_stats_views_null=filter_stats_views_null,
#         filter_comment_media_id=filter_comment_media_id,
#         filter_comment_media_account_id=filter_comment_media_account_id,
#     )
#     result = session.execute(stmt)
#
#     # pylint: disable=not-an-iterable
#     yield from call_result(result, mode)
#
#
# def iter_media(
#     session: Session,
#     mode: IterMode = IterMode.SCALARS,
#     limit: int = 0,
#     offset: int = 0,
#     order_by: MediaOrder = MediaOrder.CREATED,
#     order_asc: bool = False,
#     filter_account: str | int | list[str] | list[int] | None = None,
#     filter_created: tuple[datetime, datetime] | None = None,
# ):
#     stmt = query_media(
#         limit=limit,
#         offset=offset,
#         order_by=order_by,
#         order_asc=order_asc,
#         filter_created=filter_created,
#         filter_account=filter_account,
#     )
#     result = session.execute(stmt)
#
#     # pylint: disable=not-an-iterable
#     yield from call_result(result, mode)
#
#
# def iter_media_comments(
#     session: Session,
#     mode: IterMode = IterMode.SCALARS,
#     limit: int = 0,
#     offset: int = 0,
#     order_by: MediaCommentOrder = MediaCommentOrder.CREATED,
#     order_asc: bool = False,
#     filter_created: tuple[datetime, datetime] | None = None,
#     filter_account: str | int | list[str] | list[int] | None = None,
#     filter_media_account: int | list[int] | None = None,
# ):
#     stmt = select(MediaComment)
#     stmt = query_media_comments(
#         stmt,
#         limit=limit,
#         offset=offset,
#         order_by=order_by,
#         order_asc=order_asc,
#         filter_created=filter_created,
#         filter_account=filter_account,
#         filter_media_account=filter_media_account,
#     )
#     result = session.execute(stmt)
#
#     # pylint: disable=not-an-iterable
#     yield from call_result(result, mode)
