from typing import Any, Iterator

from datetime import datetime
from urllib import parse as url_parse

from pyyoutube import Api

from metrico import models
from metrico.hunting.utils import MultiObjCaller

from .basic import BasicHunter


class YoutubeHunter(BasicHunter):
    def __init__(self, config: dict):
        super().__init__(config)
        self.api = self._create_api()

    def _create_api(self):
        if key := self.config.get("key"):
            return Api(api_key=key)
        return None

    def _find_accounts(self, name: str, amount: int = 10, full: bool = False) -> Iterator[models.Account]:
        result = self.api.search_by_keywords(q=name, search_type=["channel"], count=amount)
        for item in result.items:
            if full:
                if account := self.get_account_data(item.id.channelId):
                    yield account
            else:
                yield models.Account(identifier=item.id.channelId, info=models.AccountInfo(name=item.snippet.title, bio=item.snippet.description))

    def analyze(self, value: Any, amount: int = 10, full: bool = False) -> Iterator[models.Account | models.Media]:
        if isinstance(value, str):
            url = url_parse.urlparse(value)
            if url.hostname and url.hostname.find("youtube") != -1:
                if url.path.find("watch") != -1:
                    query = url_parse.parse_qs(url.query)
                    query_values = query.get("v")
                    if query_values is None:
                        return
                    media = self.get_media_data(query_values[0])
                    if full and media and media.account:
                        media.account = self.get_account_data(media.account.identifier)
                    if media is not None:
                        yield media
                else:
                    yield from self._find_accounts(url.path[1:], amount, full)
            else:
                yield from self._find_accounts(value, amount, full)

    def get_account_data(self, identifier: str) -> models.Account | None:
        channel_by_id = self.api.get_channel_info(channel_id=identifier)
        if channel_by_id is None or channel_by_id.items is None or len(channel_by_id.items) == 0:
            return None

        subscriptions = None
        if self.config.get("load_subscription", False):
            iter_subscriptions = self.iter_account_subscriptions(identifier, amount=0)
            subscriptions = len(list(iter_subscriptions)) if iter_subscriptions is not None else None

        return models.Account(
            identifier=identifier,
            created=models.Created(datetime.fromisoformat(channel_by_id.items[0].snippet.publishedAt[:19])),
            info=models.AccountInfo(name=channel_by_id.items[0].snippet.title, bio=channel_by_id.items[0].snippet.description),
            stats=models.AccountStats(
                medias=int(channel_by_id.items[0].statistics.videoCount or 0),
                views=int(channel_by_id.items[0].statistics.viewCount or 0),
                followers=int(channel_by_id.items[0].statistics.subscriberCount or 0),
                subscriptions=subscriptions,
            ),
        )

    def get_media_data(self, identifier: str) -> models.Media | None:
        videos = self.api.get_video_by_id(video_id=identifier)
        if videos is None or not videos.items:
            return None

        video = videos.items[0]
        return models.Media(
            identifier=identifier,
            media_type=models.MediaType.VIDEO,
            account=models.Account(identifier=video.snippet.channelId),
            created=models.Created(datetime.strptime(video.snippet.publishedAt, "%Y-%m-%dT%H:%M:%SZ")),
            info=models.MediaInfo(title=video.snippet.title, caption=video.snippet.description, disable_comments=video.statistics.commentCount is None),
            stats=models.MediaStats(
                comments=int(video.statistics.commentCount or 0),
                likes=int(video.statistics.likeCount or 0),
                views=int(video.statistics.viewCount or 0),
            ),
        )

    def iter_account_media(self, identifier: str, amount=0):
        channel_by_id = self.api.get_channel_info(channel_id=identifier)
        if int(channel_by_id.items[0].statistics.videoCount) == 0:
            return

        playlist_id = channel_by_id.items[0].contentDetails.relatedPlaylists.uploads
        if playlist_id is None:
            return

        playlist = self.api.get_playlist_items(playlist_id=playlist_id, count=amount or None)
        for item in playlist.items:
            yield self.get_media_data(item.contentDetails.videoId)

    def iter_account_subscriptions(self, identifier: str, amount: int = 0) -> Iterator[models.Subscription]:
        try:
            subscription_by_channel = self.api.get_subscription_by_channel(channel_id=identifier, count=amount or None)
            if subscription_by_channel.items is None:
                return
        except:
            return
        for subscription in subscription_by_channel.items:
            if subscription.snippet is None:
                continue
            yield models.Subscription(
                account=models.Account(
                    identifier=subscription.snippet.resourceId.channelId,
                    info=models.AccountInfo(name=subscription.snippet.title or None, bio=subscription.snippet.description or None),
                    stats=models.AccountStats(medias=subscription.contentDetails.totalItemCount or None),
                )
            )

    def iter_media_comments(self, identifier: str, amount: int = 0) -> Iterator[models.MediaComment]:
        def get_comment_data(comment) -> models.MediaComment:
            account = None
            if comment.snippet.authorChannelId is not None:
                account = models.Account(
                    identifier=comment.snippet.authorChannelId.value, info=models.AccountInfo(name=comment.snippet.authorDisplayName or None)
                )
            return models.MediaComment(
                identifier=comment.id,
                account=account,
                content=models.MediaCommentContent(
                    text=comment.snippet.textDisplay,
                    likes=comment.snippet.likeCount,
                    created_at=datetime.strptime(comment.snippet.publishedAt, "%Y-%m-%dT%H:%M:%SZ"),
                ),
            )

        try:
            comments = self.api.get_comment_threads(video_id=identifier, count=amount or None)
        except:
            return

        for thread in comments.items:
            yield get_comment_data(thread.snippet.topLevelComment)
            if thread.replies:
                total_reply_count = int(thread.snippet.totalReplyCount)
                if total_reply_count > len(thread.replies.comments):
                    thread_comment = self.api.get_comments(parent_id=thread.id, count=None)
                    for item in thread_comment.items:
                        yield get_comment_data(item)
                else:
                    for item in thread.replies.comments:
                        yield get_comment_data(item)


class YoutubeHunterMulti(YoutubeHunter):
    def _create_api(self):
        if keys := self.config.get("keys"):
            return MultiObjCaller(cls=Api, kwargs=[{"api_key": key} for key in keys])
        raise Exception("Fail to create api!")
