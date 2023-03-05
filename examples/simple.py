from metrico.core import MetricoConfig, MetricoCore
from metrico.core.utils import BasicClassConfig

# create metrico config (database and youtube api key)
config = MetricoConfig()
config.db.url = f"sqlite://"
config.hunters["youtube"] = BasicClassConfig(config={"key": "AIzaSyDXnm6hi..."})

# create metrico object with locale config
metrico = MetricoCore(config=config)
# setup database
metrico.db.setup()

# # find some youtube channel and add them to your database
# # 1. find som accounts with the youtube hunter aka youtube api
# results = list(metrico.hunter["youtube"].analyze("distrotube"))
# # 2. we will take the first result
# account = metrico.db.create("youtube", results[0])
#
# # this will make from the hunter result a database object
# print(type(results[0]), type(account))
#
# # there is only on account in your database.
# print("Account:", metrico.db.stats("Account"))
# print("Media:  ", metrico.db.stats("Media"))
#
# # but we can add all videos uploads
# metrico.update_account(account.id, media_count=50)
#
# # check if there are more medias
# print("Account:", metrico.db.stats("Account"))
# print("Media:  ", metrico.db.stats("Media"))
#
# # we can also add all users subscription accounts to get more accounts
# metrico.update_account(account.id, subscription_count=0)
#
# # check if there are more medias
# print("Account:", metrico.db.stats("Account"))
# print("Media:  ", metrico.db.stats("Media"))
#
# # to list all medias aka videos, we need a query object
# query = MediaQuery(limit=5)
# for media in metrico.db.iter_query(query):
#     print(f"{media.created_at} {media.stats_comments:>4} {media.stats_likes:>5} {media.stats_views:>6} {media.info_title}")
