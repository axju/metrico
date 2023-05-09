# ruff: noqa: F821
from typing import Optional

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from metrico.schemas import ModelStatus

from .basic import Base


class Account(Base):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    status: Mapped[ModelStatus] = mapped_column(default=ModelStatus.OKAY)
    platform: Mapped[str]

    identifier: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    subscriptions_last_update: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    # medias_last_update: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    info_last_update: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    info_name: Mapped[Optional[str]]
    info_bio: Mapped[Optional[str]]

    stats_last_update: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    stats_medias: Mapped[Optional[int]]
    stats_views: Mapped[Optional[int]] = mapped_column(BigInteger(), nullable=True)
    stats_followers: Mapped[Optional[int]] = mapped_column(BigInteger(), nullable=True)
    stats_subscriptions: Mapped[Optional[int]] = mapped_column(BigInteger(), nullable=True)

    medias: Mapped[list["Media"]] = relationship(  # type: ignore
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="Media.created_at.desc()",
        lazy="dynamic",
    )

    comments: Mapped[list["MediaComment"]] = relationship(  # type: ignore
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="MediaComment.timestamp.desc()",
        lazy="dynamic",
    )

    subscriptions: Mapped[list["AccountSubscription"]] = relationship(
        foreign_keys="AccountSubscription.account_id",
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="AccountSubscription.timestamp.desc()",
        lazy="dynamic",
    )
    followers: Mapped[list["AccountSubscription"]] = relationship(
        foreign_keys="AccountSubscription.subscribed_account_id",
        back_populates="subscribed_account",
        cascade="all, delete-orphan",
        order_by="AccountSubscription.timestamp.desc()",
        lazy="dynamic",
    )
    info: Mapped[list["AccountInfo"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="AccountInfo.timestamp.desc()",
        lazy="dynamic",
    )
    stats: Mapped[list["AccountStats"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="AccountStats.timestamp.desc()",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"Account(id={self.id}, status={self.status!r} platform={self.platform}, identifier={self.identifier})"


class AccountSubscription(Base):
    __tablename__ = "account_subscription"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    account: Mapped["Account"] = relationship(foreign_keys="AccountSubscription.account_id", back_populates="subscriptions")
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))

    subscribed_account: Mapped["Account"] = relationship(
        foreign_keys="AccountSubscription.subscribed_account_id",
        back_populates="followers",
    )
    subscribed_account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))

    def __repr__(self) -> str:
        return f"AccountSubscription(timestamp={self.timestamp!r}, subscribed_account_id={self.subscribed_account_id!r})"


class AccountInfo(Base):
    __tablename__ = "account_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    account: Mapped["Account"] = relationship(back_populates="info")
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))
    name: Mapped[Optional[str]]
    bio: Mapped[Optional[str]]

    def __repr__(self) -> str:
        return f"AccountInfo(timestamp={self.timestamp!r}, name={self.name!r})"


class AccountStats(Base):
    __tablename__ = "account_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    account: Mapped["Account"] = relationship(back_populates="stats")
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))

    medias: Mapped[Optional[int]]
    views: Mapped[Optional[int]] = mapped_column(BigInteger(), nullable=True)
    followers: Mapped[Optional[int]] = mapped_column(BigInteger(), nullable=True)
    subscriptions: Mapped[Optional[int]] = mapped_column(BigInteger(), nullable=True)

    def __repr__(self) -> str:
        return f"AccountStats(timestamp={self.timestamp!r}, media_count={self.medias!r}, followers={self.followers!r}, subscriptions={self.subscriptions!r})"
