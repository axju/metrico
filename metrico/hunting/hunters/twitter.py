# pylint: disable=import-error
from datetime import datetime

from pytwitter import Api
from pytwitter.models.tweet import Tweet as TweetModel

from metrico.models import MediaType

from .basic import BasicHunter


class TwitterHunter(BasicHunter):
    def __init__(self, config: dict):
        super().__init__(config)
        self.api = Api(bearer_token=self.config["TWITTER_KEY"])

    def _update_config(self):
        self.api = Api(bearer_token=self.config["TWITTER_KEY"])

    def analyze(self, value: str, amount: int = 10, full: bool = False):
        result = self.api.get_users(usernames=value, user_fields=["description"])
        for item in result.data:
            yield {
                "identifier": item.id,
                "name": item.name,
                "bio": item.description,
            }

    def get_account_data(self, identifier: str):
        result = self.api.get_user(
            user_id=identifier,
            user_fields=["created_at", "description", "public_metrics"],
        )
        return {
            "identifier": result.data.id,
            "name": result.data.name,
            "bio": result.data.description,
            "created_at": datetime.fromisoformat(result.data.created_at[:19]),
            "medias": result.data.public_metrics.tweet_count,
            "followers": result.data.public_metrics.followers_count,
            "subscriptions": result.data.public_metrics.following_count,
        }

    def iter_account_media(self, identifier: str, amount: int = 0):
        result = self.api.get_timelines(user_id=identifier, tweet_fields=["created_at", "public_metrics"], max_results=amount)
        for item in result.data:
            if not isinstance(item, TweetModel):
                continue
            yield {
                "identifier": item.id,
                "media_type": MediaType.TEXT,
                "title": "",
                "caption": item.text,
                "disable_comments": False,
                "created_at": datetime.fromisoformat(item.created_at[:19]),
                "comments": item.public_metrics.reply_count,
                "likes": item.public_metrics.like_count,
                "views": item.public_metrics.impression_count,
            }
