import math
from datetime import datetime, timedelta

import matplotlib.pyplot as plt

from metrico import MetricoCore
from metrico.database import crud
from metrico.database.query import MediaOrder, MediaQuery


def normal(values):
    values_max = max(values)
    return [item / values_max for item in values]


def get_dot(comments, likes, views):
    norm = math.sqrt((comments**2) + (likes**2) + (views**2))
    ratios = [comments / likes, likes / views, comments / views]
    ratios_norm = math.sqrt(sum([value**2 for value in ratios]))
    return ((comments * ratios[0]) + (likes * ratios[1]) + (views * ratios[2])) / (norm * ratios_norm)


def get_values(media):
    timestamp, dots = [], []
    for stat in media.stats:
        if stat.comments == 0 or stat.likes == 0 or stat.views == 0:
            continue
        timestamp.insert(0, (stat.timestamp - media.created_at).total_seconds() / 60 / 60)
        dots.insert(0, get_dot(stat.comments, stat.likes, stat.views))
    return timestamp, dots


def add_query_to_plt(query):
    for item in metrico.db.iter_query(query):
        if item.stats.count() < 5 or item.stats_comments < 5:
            continue
        item_values = get_values(item)
        plt.plot(item_values[0], item_values[1], label=f"{item.id}:{item.account.info_name}")


media_id = 46578
# only if media ist 2 days old
created = (datetime.now() - timedelta(days=900), datetime.now() - timedelta(days=4))

metrico = MetricoCore.default()

plt.figure()

# plt.subplot(211)
plt.title("last 10 medias")
# add_query_to_plt(MediaQuery(limit=10, order_by=MediaOrder.CREATED, created=created))

# plt.subplot(212)
# plt.title("Paluten id=53")
add_query_to_plt(MediaQuery(limit=10, order_by=MediaOrder.CREATED, created=created, accounts=53))

plt.axis((4, 100, 0, 0.5))
plt.legend(loc="upper right")
# plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.show()
