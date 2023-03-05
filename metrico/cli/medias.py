from rich.live import Live
from rich.table import Column, Table

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
    return headers


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
        rise = [0, 0, 0]
        for index in range(2, media.stats.count()):
            value = [
                media.stats[index - 1].comments - media.stats[index].comments,
                media.stats[index - 1].likes - media.stats[index].likes,
                media.stats[index - 1].views - media.stats[index].views,
            ]
            for i in range(3):
                if value[i] < 0:
                    rise[i] += -value[i]

        values += [
            f"{rise[0]}",
            f"{rise[1]}",
            f"{rise[2]}",
        ]
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
    sub_list.add_argument("--show_lost", action="store_true", help="Show total rising/falling stats values")
    sub_list.add_argument("--dt", type=int, default=0, help="Set dt [h] for the changing stats")

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
