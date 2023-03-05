from datetime import datetime, timedelta

import matplotlib.pyplot as plt

from metrico import MetricoCore
from metrico.database import crud
from metrico.database.query import MediaOrder, MediaQuery


def normal(values):
    values_max = max(values)
    return [item / values_max for item in values]


def get_values(media):
    timestamp, views, likes, comments = [], [], [], []
    for stat in media.stats:
        timestamp.insert(0, (stat.timestamp - media.created_at).total_seconds() / 60 / 60)
        views.insert(0, stat.views)
        likes.insert(0, stat.likes)
        comments.insert(0, stat.comments)
    return timestamp, normal(views), normal(likes), normal(comments)


def add_query_to_plt(query):
    for item in metrico.db.iter_query(query):
        if item.stats.count() < 5:
            continue
        item_values = get_values(item)
        plt.plot(item_values[0], item_values[1], "r", item_values[0], item_values[2], "b", item_values[0], item_values[3], "g")


media_id = 46578
# only if media ist 2 days old
created = (datetime.now() - timedelta(days=900), datetime.now() - timedelta(days=4))

metrico = MetricoCore.default()

plt.figure()

plt.subplot(211)
plt.title("last 10 medias")
add_query_to_plt(MediaQuery(limit=10, order_by=MediaOrder.CREATED, created=created))

plt.subplot(212)
plt.title("Paluten id=53")
add_query_to_plt(MediaQuery(limit=10, order_by=MediaOrder.CREATED, created=created, accounts=53))

plt.show()
