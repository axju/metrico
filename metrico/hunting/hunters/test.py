# type: ignore
from typing import Iterator

import random
from datetime import datetime
from logging import getLogger

from faker import Faker  # pylint: disable=import-error

from metrico import models

from .basic import BasicHunter

logger = getLogger(__name__)


class TestHunter(BasicHunter):
    def __init__(self, config: dict):
        super().__init__(config)
        self.fake = Faker()
        self.accounts: list[models.Account] = []
        self.medias: list[list[models.Media]] = []
        self.comments: list[list[models.MediaComment]] = []

    def analyze(self, value: str, amount: int = 10, full: bool = False) -> Iterator[models.Account | models.Media]:
        for index in range(amount):
            yield self.get_account_data(str(index))

    def get_account_data(self, identifier: str) -> models.Account:
        index = int(identifier)
        if index in range(len(self.accounts)):
            account = self.accounts[index]
        else:
            medias = self.config.get("max_medias", 10)
            if self.config.get("random_medias", False):
                medias = random.randint(0, self.config.get("max_medias", 10))

            followers = int(medias * random.randint(1, 500) / 100)
            views = int(followers * medias * random.randint(1, 400) / 100)
            account = models.Account(
                identifier=identifier,
                created=models.Created(self.fake.date_of_birth(maximum_age=10)),
                info=models.AccountInfo(
                    name=self.fake.name(),
                    bio=self.fake.text(),
                ),
                stats=models.AccountStats(medias=medias, views=views, followers=followers, subscriptions=random.randint(0, 50)),
            )
            self.accounts.append(account)
            self.medias.append([])

        if random.random() <= self.config.get("change_account_name", 0):
            account.info.name = self.fake.name()
        if random.random() <= self.config.get("change_account_bio", 0):
            account.info.bio = self.fake.text()

        add = self.config.get("medias_add", 1)
        if random.random() <= self.config.get("change_account_medias", 0):
            account.stats.medias += add
        if random.random() <= self.config.get("change_account_stats", 0):
            account.stats.followers += int(1 + 3 * add * random.random())
            account.stats.views += int(1 + 5 * add * random.random())
        return account

    def get_media_data(self, identifier: str) -> models.Media | None:
        account_index, media_index = map(int, identifier.split(":"))
        if media_index in range(len(self.medias[account_index])):
            media = self.medias[account_index][media_index]
        else:
            media = models.Media(identifier=identifier, media_type=models.MediaType.VIDEO, account=self.accounts[account_index])
            media.created = models.Created(self.fake.date_time_between_dates(self.accounts[account_index].created.value, datetime.now()))
            media.info = models.MediaInfo(
                title=self.fake.text(max_nb_chars=random.randint(10, 40))[:-1],
                caption="\n".join(self.fake.paragraphs(nb=7)),
                disable_comments=random.random() < 0.01,
            )
            comments = self.config.get("max_comments", 10)
            if self.config.get("random_comments", False):
                comments = random.randint(0, self.config.get("max_comments", 100))
            media.stats = models.MediaStats(
                comments=comments,
                likes=random.randint(0, 1000),
                views=random.randint(0, 1000),
            )
            self.medias[account_index].append(media)
            self.comments.append([])

        if random.random() < self.config.get("change_media_title", 0):
            media.info.title = self.fake.text(max_nb_chars=random.randint(10, 40))[:-1]
        if random.random() < self.config.get("change_media_caption", 0):
            media.info.caption = "\n".join(self.fake.paragraphs(nb=7))

        add = self.config.get("comments_add", 1)
        if random.random() <= self.config.get("change_media_comments", 0):
            media.stats.comments += add
        if random.random() <= self.config.get("change_media_stats", 0):
            media.stats.likes += int(1 + 3 * add * random.random())
            media.stats.views += int(1 + 5 * add * random.random())
        return media

    def iter_account_media(self, identifier: str, amount=0):
        for index in range(self.accounts[int(identifier)].stats.medias):
            yield self.get_media_data(f"{identifier}:{index}")

    # def iter_account_subscriptions(self, identifier: str, amount: int = 0) -> Iterator[models.Subscription]:´
    #     ...

    def iter_media_comments(self, identifier: str, amount: int = 0) -> Iterator[models.MediaComment]:
        def get_comment_data(comment_index: int) -> models.MediaComment:
            if comment_index in range(len(self.comments[media_index])):
                comment = self.comments[media_index][comment_index]
            else:
                comment = models.MediaComment(identifier=f"{media_index}:{comment_index}")
                comment.account = self.get_account_data(str(len(self.accounts)))
                comment.content = models.MediaCommentContent(
                    text=self.fake.text(max_nb_chars=random.randint(10, 40))[:-1],
                    likes=random.randint(0, 1000),
                    created_at=self.fake.date_time_between_dates(self.medias[account_index][media_index].created.value, datetime.now()),
                )
                self.comments[media_index].append(comment)
            return comment

        account_index, media_index = map(int, identifier.split(":"))
        for index in range(self.medias[account_index][int(media_index)].stats.comments):
            yield get_comment_data(index)
