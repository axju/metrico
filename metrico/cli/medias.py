import math

import numpy as np
from rich.live import Live
from rich.table import Column, Table
from scipy.stats import shapiro

from metrico.analyze import get_lost
from metrico.cli.utils import MetricoBasicFilterArgumentParser, find_index, to_local_time
from metrico.core import MetricoCore
from metrico.core.utils import update_list
from metrico.database.query import MediaOrder, MediaQuery


def get_headers(args):
    headers: list[str | Column] = ["ID", "Created at", "Account", "Comments", "Likes", "Views", "Title"]
    if args.show_rel:
        for name in ["Comments", "Stats", "Info"]:
            headers.append(Column(header=name, justify="right"))
    if args.show_dt:
        for name in ["First", "Last", "DT [h]", "Comments", "Likes", "Views"]:
            headers.append(Column(header=name, justify="right"))
    if args.show_lost:
        for name in ["Comments", "Likes", "Views"]:
            headers.append(Column(header=name, justify="right"))
    if args.show_analyze:
        for name in ["C/L", "L/V", "C/V", "CLI Vector", "Ratio Vector", "Dot"]:
            headers.append(Column(header=name, justify="right"))
    if args.show_fit:
        for name in ["Comments", "Err", "Likes", "Err", "Views", "Err"]:
            headers.append(Column(header=name, justify="right"))
    return headers


def get_values_fit(media):
    if media.stats_comments < 10 or media.stats_likes < 10 or media.stats_views < 10 or media.stats.count() < 5:
        return ["-", "-", "-", "-", "-", "-"]

    timestamp, views, likes, comments = [], [], [], []
    for stat in media.stats:
        tmp = (stat.timestamp - media.created_at).total_seconds() / 60 / 60
        if tmp <= 0:
            continue
        timestamp.append(tmp)
        views.append(stat.views)
        likes.append(stat.likes)
        comments.append(stat.comments)

    timestamp = np.array(timestamp)
    views = np.array(views)
    likes = np.array(likes)
    comments = np.array(comments)

    try:
        fit_c = np.polyfit(np.log(timestamp), comments, 1)
        err_c = comments - (fit_c[0] * np.log(timestamp) + fit_c[1])

        fit_l = np.polyfit(np.log(timestamp), likes, 1)
        err_l = likes - (fit_l[0] * np.log(timestamp) + fit_l[1])

        fit_v = np.polyfit(np.log(timestamp), views, 1)
        err_v = views - (fit_v[0] * np.log(timestamp) + fit_v[1])

        # fit_c = np.polyfit(timestamp, comments, 1)
        # err_c = comments - fit_c[0] * timestamp + fit_c[1]
        #
        # fit_l = np.polyfit(timestamp, likes, 1)
        # err_l = likes - fit_l[0] * timestamp + fit_l[1]
        #
        # fit_v = np.polyfit(timestamp, views, 1)
        # err_v = views - fit_v[0] * timestamp + fit_v[1]
    except:
        return ["-", "-", "-", "-", "-", "-"]

    return [
        f"{fit_c[0]:>6.3f}",
        f"{shapiro(err_c).pvalue:>6.3f}",
        f"{fit_l[0]:>6.3f}",
        f"{shapiro(err_l).pvalue:>6.3f}",
        f"{fit_v[0]:>6.3f}",
        f"{shapiro(err_v).pvalue:>6.3f}",
    ]


def get_values_lost(media, args):
    if args.simple:
        views, likes, comments = [], [], []
        for stat in media.stats:
            tmp = (stat.timestamp - media.created_at).total_seconds() / 60 / 60
            if tmp <= 0:
                continue
            views.append(stat.views)
            likes.append(stat.likes)
            comments.append(stat.comments)

        return [
            f"{max(comments) - media.stats_comments}",
            f"{max(likes) - media.stats_likes}",
            f"{max(views) - media.stats_views}",
        ]

    return map(str, get_lost(media))


def get_values(media, args):
    values = [
        f"{media.id}",
        f"{to_local_time(media.created_at):%Y-%m-%d %H:%M}",
        # f"{to_local_time(media.stats_last_update):%Y-%m-%d %H:%M}",
        f"[{media.account_id}] {media.account.info_name[:32]}",
        f"{media.stats_comments or '-':>8}",
        f"{media.stats_likes or '-':>8}",
        f"{media.stats_views or '-':>8}",
        f"{media.info_title[:32]}",
    ]
    if args.show_rel:
        values += [
            f"{media.comments.count():>5}",
            f"{media.stats.count():>3}",
            f"{media.info.count():>3}",
        ]
    if args.show_dt:
        index_dt = media.stats.count() - 1
        if args.dt:
            index_dt = find_index(media.stats, args.dt)
        values += [
            f"{to_local_time(media.stats[index_dt].timestamp):%Y-%m-%d %H:%M}",
            f"{to_local_time(media.stats[0].timestamp):%Y-%m-%d %H:%M}",
            f"{(media.stats[0].timestamp - media.stats[index_dt].timestamp).total_seconds() / 3600:5.1f}",
            f"{media.stats[0].comments - media.stats[index_dt].comments}",
            f"{media.stats[0].likes - media.stats[index_dt].likes}",
            f"{media.stats[0].views - media.stats[index_dt].views}",
        ]
    if args.show_lost:
        values += get_values_lost(media, args)
    if args.show_analyze:
        if media.stats_comments == 0 or media.stats_likes == 0 or media.stats_views == 0:
            values += ["-", "-", "-", "-", "-", "-"]
        else:
            norm = math.sqrt((media.stats_comments**2) + (media.stats_likes**2) + (media.stats_views**2))
            ratios = [media.stats_comments / media.stats_likes, media.stats_likes / media.stats_views, media.stats_comments / media.stats_views]
            ratios_norm = math.sqrt(sum([value**2 for value in ratios]))
            dot = ((media.stats_comments * ratios[0]) + (media.stats_likes * ratios[1]) + (media.stats_views * ratios[2])) / (norm * ratios_norm)
            values += [
                f"{1000 * ratios[0]:>6.3f}",
                f"{1000 * ratios[1]:>6.3f}",
                f"{1000 * ratios[2]:>6.3f}",
                f"{media.stats_comments/norm:>6.3f}, {media.stats_likes/norm:>6.3f}, {media.stats_views/norm:>6.3f}",
                f"{ratios[0] / ratios_norm:>6.3f}, {ratios[1] / ratios_norm:>6.3f}, {ratios[2] / ratios_norm:>6.3f}",
                f"{100 * dot:6.4f}",
            ]
    if args.show_fit:
        values += get_values_fit(media)
    return values


def list_medias(metrico: MetricoCore, args):
    headers = get_headers(args)
    table = Table(*headers)
    with Live(table, refresh_per_second=4):
        for media in metrico.db.iter_query(MediaQuery.from_namespace(args)):
            values = get_values(media, args)
            table.add_row(*values)


def parse_args():
    parser = MetricoBasicFilterArgumentParser("medias")
    parser.add_argument("--order_by", type=lambda x: MediaOrder[x], choices=list(MediaOrder))

    subparsers = parser.add_subparsers(dest="action", help="sub-command help")
    sub_list = subparsers.add_parser("list")
    sub_list.add_argument("--show_rel", action="store_true", help="Show length of relationship models")
    sub_list.add_argument("--show_dt", action="store_true", help="Show stats changing")
    sub_list.add_argument("--dt", type=int, default=0, help="Set dt [h] for the changing stats")
    sub_list.add_argument("--show_lost", action="store_true", help="Show total rising/falling stats values")
    sub_list.add_argument("--simple", action="store_true", help="Make it simple")
    sub_list.add_argument("--show_analyze", action="store_true", help="Show some analyze values")
    sub_list.add_argument("--show_fit", action="store_true", help="Show the log fit values")

    sub_update = subparsers.add_parser("update")
    sub_update.add_argument("--threads", type=int, default=8)
    sub_update.add_argument("--comment_count", type=int, default=-1)

    subparsers.add_parser("count")

    metrico, args = parser.parse_args()
    return parser, metrico, args


def main() -> int:
    parser, metrico, args = parse_args()
    match args.action:
        case "list":
            list_medias(metrico, args)

        case "count":
            sub_stmt = MediaQuery.from_namespace(args)
            print(metrico.db.count_query(sub_stmt))

        case "update":
            update_list(
                [obj.id for obj in metrico.db.iter_query(MediaQuery.from_namespace(args))],
                metrico.update_account,
                args.threads,
                comment_count=args.comment_count,
            )

        case _:
            parser.print_help()

    return 0


if __name__ == "__main__":
    main()
