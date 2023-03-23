from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import lognorm, shapiro

from metrico import MetricoCore
from metrico.database import crud
from metrico.database.query import MediaOrder, MediaQuery

media_id = 74566
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
x2 = np.linspace(0.1, max(timestamp), 100)


a, b = np.polyfit(np.log(x), comments, 1)
y2 = a * np.log(x2) + b
err = comments - (a * np.log(x) + b)

# a, b = np.polyfit(x, comments, 1)
# y2 = a * x2 + b
# err = comments - (a * x + b)

print(err)
print(np.mean(err))
print(np.std(err))
print(shapiro(err).pvalue)

plt.subplot(211)
plt.title("Comments")
plt.scatter(timestamp, comments)
plt.plot(x2, y2, "r")

plt.subplot(212)
plt.hist(err, edgecolor="black", bins=20)

plt.show()
