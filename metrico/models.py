from typing import Optional

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MediaType(Enum):
    IMAGE = 0
    VIDEO = 1
    TEXT = 2

    def __str__(self):
        return self.name


class TriggerStatus(Enum):
    WAIT = 0
    RUN = 1
    ERROR = 2

    def __str__(self):
        return self.name


class ModelStatus(Enum):
    OKAY = 0
    FAIL = 1

    def __str__(self):
        return self.name


@dataclass
class Created:
    value: Optional[datetime] = None


@dataclass
class AccountInfo:
    name: Optional[str] = None
    bio: Optional[str] = None


@dataclass
class AccountStats:
    medias: Optional[int] = None
    views: Optional[int] = None
    followers: Optional[int] = None
    subscriptions: Optional[int] = None


@dataclass
class Account:
    identifier: str
    created: Optional[Created] = None
    info: Optional[AccountInfo] = None
    stats: Optional[AccountStats] = None


@dataclass
class MediaInfo:
    title: Optional[str] = None
    caption: Optional[str] = None
    disable_comments: bool = False


@dataclass
class MediaStats:
    comments: Optional[int] = None
    likes: Optional[int] = None
    views: Optional[int] = None


@dataclass
class Media:
    identifier: str
    media_type: MediaType
    account: Optional[Account]
    created: Optional[Created] = None
    info: Optional[MediaInfo] = None
    stats: Optional[MediaStats] = None


@dataclass
class MediaCommentContent:
    text: str
    likes: int
    created_at: datetime


@dataclass
class MediaComment:
    identifier: str
    account: Optional[Account] = None
    content: Optional[MediaCommentContent] = None


@dataclass
class Subscription:
    account: Account


@dataclass
class DatabaseConfig:
    url: str = "sqlite:///database.db"
    enable_echo: bool = False
    on_create_account_trigger: str = ""
    on_create_media_trigger: str = ""


@dataclass
class BasicClassConfig:
    cls: str = ""
    config: dict = field(default_factory=lambda: {})


@dataclass
class BasicClassItem:
    config: dict
