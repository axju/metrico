from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np

from metrico import MetricoCore
from metrico.database import crud
from metrico.database.query import MediaOrder, MediaQuery


def plot_fit(x, y, x2):
    fit = np.polyfit(np.log(x), y, 1)
    y2 = fit[1] + fit[0] * np.log(x2)
    plt.plot(x2, y2, "r")


media_id = 74536
metrico = MetricoCore.default()


timestamp, views, likes, comments = [], [], [], []
with metrico.db.Session() as session:
    media = crud.get_media(session, media_id)
    for stat in media.stats:
        tmp = (stat.timestamp - media.created_at).total_seconds() / 60 / 60
        if tmp <= 0:
            continue
        timestamp.append(tmp)
        views.append(stat.views)
        likes.append(stat.likes)
        comments.append(stat.comments)

x = np.array(timestamp)
x2 = np.linspace(1, max(timestamp), 100)


plt.subplot(311)
plt.title("Comments")
plt.scatter(timestamp, comments)
plot_fit(timestamp, comments, x2)

plt.subplot(312)
plt.title("likes")
plt.scatter(timestamp, likes)
plot_fit(timestamp, likes, x2)

plt.subplot(313)
plt.title("views")
plt.scatter(timestamp, views)
plot_fit(timestamp, views, x2)

plt.show()
