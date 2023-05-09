from datetime import datetime, timedelta
from time import sleep

import matplotlib.pyplot as plt
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


def iter_comments(db: MetricoDB, query: MediaCommentQuery, start: datetime, end: datetime, dt: timedelta = timedelta(days=1)):
    current = start
    while current < end:
        query.created = (current, current + dt)
        yield current, list(db.iter_query(query))
        current += dt


# start = datetime(2022, 1, 1)
# end = datetime(2022, 2, 1)
# dt = timedelta(days=1)
#
# db = MetricoDB.default()
#
# current = start
# while current < end:
#     with Live() as live:
#         created = (current, current + dt)
#         query = MediaCommentQuery(limit=20, media_account_id=1, order_by=MediaCommentOrder.LIKES, created=created)
#         comments = [[f"{comment.account.info_name}", f"{comment.media.account.info_name[:32]}", f"{comment.likes}", f"{comment.text[:100]}"] for comment in db.iter_query(query)]
#         # for comment in db.iter_query(query):
#         #     print(comment)
#
#         live.update(show_data(comments))
#         sleep(0.5)
#
#     current += dt


def plot_comments(media_account_id, h=5):
    query = MediaCommentQuery(media_account_id=media_account_id, order_by=MediaCommentOrder.LIKES)
    x, y = [], []
    for no, comments in iter_comments(db, query, datetime(2022, 1, 1), datetime(2023, 1, 1), timedelta(days=1)):
        print(no, len(comments))
        x.append(no)
        y.append(len(comments))

    x2 = x[h:]
    y2 = [sum(y[i : i + h]) for i in range(len(y) - h)]
    plt.plot(x, y, "k.")
    plt.plot(x2, y2, "r")


db = MetricoDB.default()
plt.figure()
plt.subplot(211)
plot_comments(1)
plt.subplot(212)
plot_comments(194673)
plt.show()
