from datetime import datetime, timedelta
from time import sleep

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from rich.live import Live
from rich.table import Table

from metrico import MetricoDB
from metrico.database import MediaCommentOrder, MediaCommentQuery

# renzo     -> id=1
# schlumpf  -> id=194673


def show_data(data):
    table = Table()
    for row in data:
        table.add_row(*row)
    return table


def iter_comments(
    db: MetricoDB, query: MediaCommentQuery, start: datetime, end: datetime, dt: timedelta = timedelta(hours=1), interval: timedelta = timedelta(days=30)
):
    current = start
    while current < end:
        query.created = (start - interval, current)
        data = {}
        for item in db.iter_query(query):
            data[item.media.id] = data.get(item.media.id, 0) + 1
        yield current, sorted(data.items(), key=lambda x: x[1], reverse=True)
        current += dt


db = MetricoDB.default()
colors = list(mcolors.XKCD_COLORS.values())
query = MediaCommentQuery(media_account_id=1, order_by=MediaCommentOrder.LIKES)
for no, (current, items) in enumerate(iter_comments(db, query, datetime(2022, 1, 1), datetime(2023, 1, 1), dt=timedelta(hours=4))):
    path = f"out/{no:04d}.png"
    print(current, path, items)
    y = [item[0] for item in items[:10]]
    x = [item[1] for item in items[:10]]
    plt.rcdefaults()
    fig, ax = plt.subplots()
    y_pos = np.arange(len(x))
    bars = ax.barh(y_pos, x)
    ax.bar_label(bars)

    ax.barh(list(range(10)), x, align="center", color=[colors[index] for index in y])
    ax.set_yticks(y_pos, labels=[item[0] for item in items[:10]])

    ax.invert_yaxis()
    plt.savefig(path)
    # plt.show()
