from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from metrico.schemas import TriggerStatus

from .basic import Base

if TYPE_CHECKING:
    from .account import Account
    from .media import Media


class Trigger(Base):
    __tablename__ = "trigger"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    name: Mapped[str]
    status: Mapped[TriggerStatus] = mapped_column(default=TriggerStatus.WAIT)

    accounts: Mapped[list["TriggerAccount"]] = relationship(
        cascade="all, delete-orphan",
        # order_by="TriggerAccount.timestamp.asc()",
        lazy="dynamic",
    )
    medias: Mapped[list["TriggerMedia"]] = relationship(
        cascade="all, delete-orphan",
        # order_by="TriggerMedia.timestamp.asc()",
        lazy="dynamic",
    )
    stats: Mapped[list["TriggerStats"]] = relationship(
        cascade="all, delete-orphan",
        order_by="TriggerStats.timestamp.desc()",
        lazy="dynamic",
    )


class TriggerAccount(Base):
    __tablename__ = "trigger_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    trigger_id: Mapped[int] = mapped_column(ForeignKey("trigger.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))

    trigger: Mapped[list["Trigger"]] = relationship(back_populates="accounts")
    account: Mapped[list["Account"]] = relationship()


class TriggerMedia(Base):
    __tablename__ = "trigger_media"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    trigger_id: Mapped[int] = mapped_column(ForeignKey("trigger.id"))
    media_id: Mapped[int] = mapped_column(ForeignKey("media.id"))

    trigger: Mapped[list["Trigger"]] = relationship(back_populates="medias")
    media: Mapped[list["Media"]] = relationship()


class TriggerStats(Base):
    __tablename__ = "trigger_stats"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    trigger_id: Mapped[int] = mapped_column(ForeignKey("trigger.id"))

    started: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    finished: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    success: Mapped[bool] = mapped_column(default=False)
