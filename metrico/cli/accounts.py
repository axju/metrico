# type: ignore
from rich.live import Live
from rich.table import Column, Table

from metrico.analyze import get_lost
from metrico.cli.utils import MetricoBasicFilterArgumentParser, find_index
from metrico.core import MetricoCore
from metrico.core.utils import update_list
from metrico.database.query import AccountOrder, AccountQuery


def list_accounts(metrico: MetricoCore, args):
    headers = [
        Column(header="ID", justify="right"),
        "Status",
        "Platform",
        "Name",
        Column(header="Medias", justify="right"),
        Column(header="Views", justify="right"),
        Column(header="Followers", justify="right"),
        Column(header="Subscriptions", justify="right"),
    ]
    if args.show_rel:
        for name in ["Stats", "Info", "Comments", "Medias", "Followers", "Subscriptions"]:
            headers.append(Column(header=name, justify="right"))
    if args.show_dt:
        for name in ["First", "Last", "DT [h]", "Medias", "Views", "Followers", "Subscriptions"]:
            headers.append(Column(header=name, justify="right"))
    if args.show_lost:
        for name in ["Comments", "Likes", "Views"]:
            headers.append(Column(header=name, justify="right"))
    table = Table(
        *headers,
        expand=True,
        style="magenta",
        show_lines=True,
        # row_styles=["magenta", "white on magenta dim"],
    )
    with Live(table, refresh_per_second=4):
        account_query = AccountQuery.from_namespace(args)
        for account in metrico.db.iter_query(account_query):
            values = [
                f"{account.id}",
                f"{account.status}",
                f"{account.platform}",
                f"{account.info_name or '-'}",
                f"{account.stats_medias or '-'}",
                f"{account.stats_views or '-'}",
                f"{account.stats_followers or '-'}",
                f"{account.stats_subscriptions or '-'}",
            ]
            if args.show_rel:
                values += [
                    f"{account.stats.count():>3}",
                    f"{account.info.count():>3}",
                    f"{account.comments.count()}",
                    f"{account.medias.count()}",
                    f"{account.followers.count()}",
                    f"{account.subscriptions.count()}",
                ]
            if args.show_dt and account.stats.count():
                index_dt = account.stats.count() - 1
                if args.dt:
                    index_dt = find_index(account.stats, args.dt)
                values += [
                    f"{account.stats[index_dt].timestamp:%Y-%m-%d %H:%M}",
                    f"{account.stats[0].timestamp:%Y-%m-%d %H:%M}",
                    f"{(account.stats[0].timestamp - account.stats[index_dt].timestamp).total_seconds() / 3600:5.1f}",
                    f"{account.stats[0].medias - account.stats[index_dt].medias}",
                    f"{(account.stats[0].views or 0) - (account.stats[index_dt].views or 0)}",
                    f"{(account.stats[0].followers or 0) - (account.stats[index_dt].followers or 0)}",
                    f"{(account.stats[0].subscriptions or 0) - (account.stats[index_dt].subscriptions or 0)}",
                ]
            if args.show_lost:
                lost_total = [0, 0, 0]
                for media in account.medias.limit(args.lost_limit):
                    lost = get_lost(media)
                    for i in range(3):
                        lost_total[i] += lost[i]
                values += [f"{lost_total[0]}", f"{lost_total[1]}", f"{lost_total[2]}"]

            table.add_row(*values)


def parse_args():
    parser = MetricoBasicFilterArgumentParser("accounts")
    parser.add_argument("--order_by", type=lambda x: AccountOrder[x], choices=list(AccountOrder))
    parser.add_argument("--filter_stats_null", action="store_true")
    parser.add_argument("--filter_stats_views_null", action="store_true")
    parser.add_argument("--filter_comment_media_id", nargs="*", type=int)
    parser.add_argument("--filter_comment_media_account_id", nargs="*", type=int)

    subparsers = parser.add_subparsers(dest="action", help="sub-command help")
    sub_list = subparsers.add_parser("list")
    sub_list.add_argument("--show_rel", action="store_true", help="Show length of relationship models")
    sub_list.add_argument("--show_dt", action="store_true", help="Show stats changing")
    sub_list.add_argument("--dt", type=int, default=0, help="Set dt [h] for the changing stats")
    sub_list.add_argument("--show_lost", action="store_true", help="Show lost values of account medias")
    sub_list.add_argument("--lost_limit", type=int, default=50, help="Limit for the medias")

    sub_update = subparsers.add_parser("update")
    sub_update.add_argument("--threads", type=int, default=8)
    sub_update.add_argument("--media_count", type=int, default=-1)
    sub_update.add_argument("--comment_count", type=int, default=-1)
    sub_update.add_argument("--subscription_count", type=int, default=-1)

    subparsers.add_parser("count")

    metrico, args = parser.parse_args()
    return parser, metrico, args


def main() -> int:
    parser, metrico, args = parse_args()
    match args.action:
        case "list":
            list_accounts(metrico, args)

        case "count":
            sub_stmt = AccountQuery.from_namespace(args)
            print(metrico.db.count_query(sub_stmt))

        case "update":
            update_list(
                [obj.id for obj in metrico.db.iter_query(AccountQuery.from_namespace(args))],
                metrico.update_account,
                args.threads,
                media_count=args.media_count,
                comment_count=args.comment_count,
                subscription_count=args.subscription_count,
            )

        case _:
            parser.print_help()

    return 0


if __name__ == "__main__":
    main()
