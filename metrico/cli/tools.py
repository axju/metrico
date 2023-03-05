# type: ignore
from typing import Any

import random
import string
import sys
import time
from datetime import datetime
from pathlib import Path

from rich import print as rich_print
from rich.live import Live
from rich.table import Table

from metrico import MetricoCore, schemas
from metrico.cli.utils import MetricoArgumentParser, console
from metrico.database import models


def get_random_string(length: int = 32) -> str:
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


def config(metrico: MetricoCore, args) -> int:
    match args.key:
        case None:
            rich_print(metrico.config)

        case str() as key:
            rich_print(f"{key} - {getattr(metrico.config, key)}")

        case _:
            print("WTF?")
            return 1
    return 0


def benchmark(metrico: MetricoCore, args) -> int:
    platform = "test"

    metrico.config.db.url = "sqlite://"
    if args.sqlite:
        Path("testing.db").unlink(missing_ok=True)
        metrico.config.db.url = "sqlite:///testing.db"
    metrico.db.reload_config()

    metrico.db.setup()
    metrico.hunter[platform].config["max_medias"] = args.medias
    metrico.hunter[platform].config["max_comments"] = args.comments
    metrico.hunter[platform].config["change_account_stats"] = 1
    metrico.hunter[platform].config["change_media_stats"] = 1

    # metrico.hunter[platform].config["random_medias"] = False
    # metrico.hunter[platform].config["random_comments"] = False
    #
    # metrico.hunter[platform].config["medias_add"] = 1
    # metrico.hunter[platform].config["change_account_name"] = 0
    # metrico.hunter[platform].config["change_account_bio"] = 0
    # metrico.hunter[platform].config["change_account_stats"] = 1
    # metrico.hunter[platform].config["change_account_medias"] = 0
    #
    # metrico.hunter[platform].config["comments_add"] = 5
    # metrico.hunter[platform].config["change_media_title"] = 0
    # metrico.hunter[platform].config["change_media_caption"] = 1
    # metrico.hunter[platform].config["change_media_stats"] = 1
    # metrico.hunter[platform].config["change_media_comments"] = 0

    console.log("Loops:", args.loops, "Accounts:", args.accounts, "Medias:", args.medias, "Comments:", args.comments)
    console.log("Database:", metrico.config.db.url)

    start = time.time()
    account_ids = []
    for data in metrico.hunter[platform].analyze("foo", amount=args.accounts):
        if isinstance(data, schemas.Account):
            account = metrico.db.create_account(platform, data)
            account_ids.append(account.id)

    for loop in range(args.loops):
        console.log(f"Running loop {loop}")
        for account_id in account_ids:
            metrico.update_account(account_id, media_count=args.media_count, comment_count=args.comment_count, subscription_count=args.subscription_count)

    end = time.time()

    stats = metrico.db.stats()
    results: dict[str, int] = {
        "Account": args.medias * args.comments + args.accounts,
        "Account-Info": args.medias * args.comments + args.accounts,
        "Account-Data": args.medias * args.comments + args.accounts + (args.loops * args.accounts),
        "Media": args.accounts * args.medias,
        "Media-Info": args.accounts * args.medias,
        "Media-Data": args.accounts * args.medias * args.loops,
        "Media-Comment": args.accounts * args.medias * args.comments,
        "Account-Subscription": 0,
    }
    error = any(stats[key] != results[key] for key in stats)

    table = Table("", *stats.keys())
    table.add_row("DB", *[str(value) for value in stats.values()])
    table.add_row("Ref", *[str(results.get(key, "")) for key in stats.keys()])

    console.print(table)
    console.print(f"Result: {end - start:.2f} sec")
    console.print(f"Error:  {error}")
    return 0


def stats_all(metrico: MetricoCore, args):
    def update_data(data):
        table = Table("Timestamp", *alchemy_map.keys())
        for row in data:
            table.add_row(*row)
        return table

    alchemy_map = {
        "Account": models.Account,
        "Account-Subscription": models.AccountSubscription,
        "Account-Info": models.AccountInfo,
        "Account-Data": models.AccountStats,
        "Media": models.Media,
        "Media-Info": models.MediaInfo,
        "Media-Data": models.MediaStats,
        "Media-Comment": models.MediaComment,
    }

    rows: list[list[str]] = []
    values_last: list[Any] = []
    with Live() as live:
        while True:
            try:
                with metrico.db.Session() as session:
                    values = [datetime.now()] + [session.query(model).count() for name, model in alchemy_map.items()]
                    if values_last:
                        values_dt = [values[i] - values_last[i] for i in range(len(values))]
                        rows.append([f"{values[0]}"] + [f"{values[i]} [{values_dt[i]/values_dt[0].total_seconds():.2f}]" for i in range(1, len(values))])
                    else:
                        rows.append([str(value) for value in values])

                    live.update(update_data(rows))
                    if not args.dynamic:
                        break

                    if len(rows) > args.limit:
                        rows = rows[-args.limit :]

                    values_last = values
                    time.sleep(args.dt)
            except KeyboardInterrupt:
                break
            except Exception as exc:
                raise exc


def show_data(datas: list[dict]):
    table = Table("NO", "Platform", "Name", "Stats")
    for index, data in enumerate(datas):
        row, item = [str(index), data["platform"]], data["item"]
        match item:
            case schemas.Account() as account:
                row.append(account.info.name)
                if item.stats:
                    row.append(f"Medias:{account.stats.medias:<4} | Followers:{account.stats.followers}")
                else:
                    row.append("-")
                if account.info.bio:
                    row.append(account.info.bio.split("\n")[0][:100])
                else:
                    row.append("-")

            case schemas.Media() as media:
                if media.account.info:
                    row.append(f"{media.account.info.name} | {media.info.title}")
                else:
                    row.append(media.info.title)
                if media.stats:
                    row.append(f"Likes:{media.stats.likes:<6} | Comments:{media.stats.comments}")
                else:
                    row.append("-")

        table.add_row(*row)
    console.print(table)


def select_index(max_index: int):
    while True:
        raw_input = input("Select NO. default=0, exit with 'e': ") or 0
        if raw_input in ["E", "e"]:
            sys.exit(1)
        try:
            index = int(raw_input)
            if index in range(max_index):
                return index
        except:
            console.print("Please enter a number!")


def add_item(metrico: MetricoCore, args):
    datas = []
    for platform, hunter in metrico.hunter.items():
        if items := hunter.analyze(args.value, full=args.full):
            datas += [{"platform": platform, "item": item} for item in items]

    if not datas:
        console.print("No data!")
        sys.exit(1)

    show_data(datas)
    index = select_index(len(datas))

    item = metrico.db.create(datas[index]["platform"], datas[index]["item"])
    console.print("create", item)


def main() -> int:
    parser = MetricoArgumentParser("utils")
    subparsers = parser.add_subparsers(dest="action", help="sub-command help")

    sub_config = subparsers.add_parser("config")
    sub_config.add_argument("key", nargs="?")

    sub_benchmark = subparsers.add_parser("benchmark")
    sub_benchmark.add_argument("loops", nargs="?", type=int, default=10)
    sub_benchmark.add_argument("accounts", nargs="?", type=int, default=2)
    sub_benchmark.add_argument("medias", nargs="?", type=int, default=5)
    sub_benchmark.add_argument("comments", nargs="?", type=int, default=5)
    sub_benchmark.add_argument("--media_count", type=int, default=0)
    sub_benchmark.add_argument("--comment_count", type=int, default=0)
    sub_benchmark.add_argument("--subscription_count", type=int, default=0)
    sub_benchmark.add_argument("--sqlite", action="store_true")

    sub_make_migrations = subparsers.add_parser("makemigrations")
    sub_make_migrations.add_argument("comment", type=str, help="Comment of migration")
    subparsers.add_parser("migrate")
    sub_stats = subparsers.add_parser("stats")
    sub_stats.add_argument("--dynamic", action="store_true")
    sub_stats.add_argument("--limit", type=int, default=10)
    sub_stats.add_argument("--dt", type=int, default=2)

    sub_add = subparsers.add_parser("add")
    sub_add.add_argument("--full", action="store_true")
    sub_add.add_argument("value")

    metrico, args = parser.parse_args()
    match args.action:
        case "config":
            return config(metrico, args)
        case "benchmark":
            return benchmark(metrico, args)
        case "makemigrations":
            metrico.db.make_migrations(message=args.comment)
        case "migrate":
            metrico.db.migrate()
        case "stats":
            stats_all(metrico, args)
        case "add":
            add_item(metrico, args)
        case _:
            parser.print_help()
            return 1
    return 0


if __name__ == "__main__":
    main()
