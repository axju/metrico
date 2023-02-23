from typing import Optional

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from metrico.models import MediaType, ModelStatus

from .account import Account
from .basic import Base


class Media(Base):
    __tablename__ = "media"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    status: Mapped[ModelStatus] = mapped_column(default=ModelStatus.OKAY)
    account: Mapped["Account"] = relationship(back_populates="medias")
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))

    identifier: Mapped[str]
    media_type: Mapped[MediaType]
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    comments_last_update: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    info_last_update: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    info_title: Mapped[Optional[str]]
    info_caption: Mapped[Optional[str]]
    info_disable_comments: Mapped[bool] = mapped_column(Boolean(), default=False)

    stats_last_update: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    stats_comments: Mapped[Optional[int]]
    stats_likes: Mapped[Optional[int]]
    stats_views: Mapped[Optional[int]] = mapped_column(BigInteger(), nullable=True)

    comments: Mapped[list["MediaComment"]] = relationship(
        back_populates="media",
        cascade="all, delete-orphan",
        order_by="MediaComment.created_at.desc()",
        lazy="dynamic",
    )
    info: Mapped[list["MediaInfo"]] = relationship(
        back_populates="media",
        cascade="all, delete-orphan",
        order_by="MediaInfo.timestamp.desc()",
        lazy="dynamic",
    )
    stats: Mapped[list["MediaStats"]] = relationship(
        back_populates="media",
        cascade="all, delete-orphan",
        order_by="MediaStats.timestamp.desc()",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"Media(id={self.id!r}, account={self.account.id!r}, info_title={self.info_title!r})"

    # def __str__(self):
    #     return f"{self.stats_likes or '-'} - {self.stats_comments or '-'} - {self.info_title or '-'}"


class MediaComment(Base):
    __tablename__ = "media_comment"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    status: Mapped[ModelStatus] = mapped_column(default=ModelStatus.OKAY)
    media: Mapped["Media"] = relationship(back_populates="comments")
    media_id: Mapped[int] = mapped_column(ForeignKey("media.id"))

    account: Mapped["Account"] = relationship(back_populates="comments")
    account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("account.id"), nullable=True)

    identifier: Mapped[str]
    text: Mapped[Optional[str]]
    likes: Mapped[Optional[int]]
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    def __repr__(self) -> str:
        return f"MediaComment(timestamp={self.timestamp}, id={self.id!r}, text={self.text!r}, likes={self.likes!r})"


class MediaInfo(Base):
    __tablename__ = "media_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    media: Mapped["Media"] = relationship(back_populates="info")
    media_id: Mapped[int] = mapped_column(ForeignKey("media.id"))

    title: Mapped[str]
    caption: Mapped[str]
    disable_comments: Mapped[bool] = mapped_column(Boolean(), default=False)

    def __repr__(self) -> str:
        return f"MediaInfo(timestamp={self.timestamp!r}, title={self.title!r}, caption={self.caption!r})"


class MediaStats(Base):
    __tablename__ = "media_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    media: Mapped["Media"] = relationship(back_populates="stats")
    media_id: Mapped[int] = mapped_column(ForeignKey("media.id"))

    comments: Mapped[Optional[int]]
    likes: Mapped[Optional[int]]
    views: Mapped[Optional[int]] = mapped_column(BigInteger(), nullable=True)

    def __repr__(self) -> str:
        return f"MediaStats(timestamp={self.timestamp!r}, comments={self.comments!r}, likes={self.likes!r})"
