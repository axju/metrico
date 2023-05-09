# type: ignore
from rich.live import Live
from rich.table import Table
from sqlalchemy import func, select

from metrico import Hunter, MetricoConfig, MetricoDB
from metrico.cli.utils import MetricoArgumentParser, to_local_time
from metrico.database import models


def account_info(db: MetricoDB, account: models.Account):
    account_fields = {
        "Name": account.info_name,
        "Bio": account.info_bio.split("\n")[0][:200] if account.info_bio else "-",
        "Medias": account.stats_medias,
        "Views": account.stats_views,
        "Followers": account.stats_followers,
        "Subscriptions": account.stats_subscriptions,
        "Update-Info": account.info_last_update,
        "Update-Stats": account.stats_last_update,
    }
    account_relations = {
        "Medias": models.Media,
        "Comments": models.MediaComment,
        "Subscriptions": models.AccountSubscription,
        "Info": models.AccountInfo,
        "Stats": models.AccountStats,
    }
    account_stats_map = {
        "Media-Comments [rel]": select(func.count(models.MediaComment.id)).join(models.Media).where(models.Media.account_id == account.id),
        "Media-Comments-Likes [rel]": select(func.sum(models.MediaComment.likes)).join(models.Media).where(models.Media.account_id == account.id),
        "Media-Comments-Accounts [rel]": select(models.Account.id, func.count(models.Account.id))
        .join(models.MediaComment, models.Account.id == models.MediaComment.account_id)
        .join(models.Media, models.Media.id == models.MediaComment.media_id)
        .where(models.Media.account_id == account.id)
        .group_by(models.Account.id),
        "Media-Comments": select(func.sum(models.Media.stats_comments)).where(models.Media.account_id == account.id),
        "Media-Likes": select(func.sum(models.Media.stats_likes)).where(models.Media.account_id == account.id),
        "Media-Views": select(func.sum(models.Media.stats_views)).where(models.Media.account_id == account.id),
    }

    print(f"ID: {account.id} - Identifier: {account.identifier} - Platform: {account.platform}")
    print("Account Values:")
    name_len = max(map(len, account_fields.keys())) + 1
    for name, value in account_fields.items():
        print(f"{name:>{name_len}}: {value}")

    print("\nAccount Relations:")
    name_len = max(map(len, account_relations.keys())) + 1
    with db.Session() as session:
        for name, model in account_relations.items():
            value = session.scalar(select(func.count(model.id)).where(model.account_id == account.id))
            print(f"{name:>{name_len}}: {value}")

    print("\nAccount Stats:")
    name_len = max(map(len, account_stats_map.keys())) + 1
    with db.Session() as session:
        for name, stmt in account_stats_map.items():
            value = session.scalar(stmt)
            print(f"{name:>{name_len}}: {value}")


def account_infos(db: MetricoDB, account: models.Account, args):
    stmt = select(models.AccountInfo).where(models.AccountInfo.account_id == account.id).order_by(models.AccountInfo.timestamp.desc()).limit(args.limit or 10)
    table = Table("ID", "Timestamp", "Name", "Bio")
    with db.Session() as session, Live(table, refresh_per_second=4):
        for value in session.execute(stmt).scalars():
            table.add_row(f"{value.id}", f"{to_local_time(value.timestamp):%Y-%m-%d %H:%M}", f"{value.name}", f"{value.bio}")


def account_stats(db: MetricoDB, account: models.Account, args):
    stmt = (
        select(models.AccountStats).where(models.AccountStats.account_id == account.id).order_by(models.AccountStats.timestamp.desc()).limit(args.limit or 10)
    )
    table = Table("ID", "Timestamp", "Medias", "Views", "Followers", "Subscriptions")
    with db.Session() as session, Live(table, refresh_per_second=4):
        for stat in session.execute(stmt).scalars():
            table.add_row(
                f"{stat.id}",
                f"{to_local_time(stat.timestamp):%Y-%m-%d %H:%M}",
                f"{stat.medias}",
                f"{stat.views}",
                f"{stat.followers}",
                f"{stat.subscriptions}",
            )


def account_subscriptions(db: MetricoDB, account: models.Account, args):
    stmt = select(models.AccountSubscription).where(models.AccountSubscription.account_id == account.id).limit(args.limit or 10)
    table = Table("ID", "Account")
    with db.Session() as session, Live(table, refresh_per_second=4):
        for subscription in session.execute(stmt).scalars():
            table.add_row(
                f"{subscription.id:>5}",
                f"[{subscription.subscribed_account.id}] {subscription.subscribed_account.info_name}",
            )


def account_followers(db: MetricoDB, account: models.Account, args):
    stmt = select(models.AccountSubscription).where(models.AccountSubscription.subscribed_account_id == account.id).limit(args.limit or 10)
    table = Table("ID", "Account")
    with db.Session() as session, Live(table, refresh_per_second=4):
        for follower in session.execute(stmt).scalars():
            table.add_row(
                f"{follower.id:>5}",
                f"[{follower.account.id}] {follower.account.info_name}",
            )


def account_comments(db: MetricoDB, account: models.Account, args):
    stmt = (
        select(models.Account, func.count(models.MediaComment.id))
        .join(models.MediaComment, models.Account.id == models.MediaComment.account_id)
        .join(models.Media, models.Media.id == models.MediaComment.media_id)
        .where(models.Media.account_id == account.id)
        .group_by(models.Account.id)
        .order_by(func.count(models.MediaComment.id).desc())
        .limit(args.limit or 10)
    )
    table = Table("Count", "Account")
    with db.Session() as session, Live(table, refresh_per_second=4):
        for value, comments in session.execute(stmt).all():
            table.add_row(f"{comments:>5}", f"[{value.id}] {value.info_name}")


def account_commented(db: MetricoDB, account: models.Account, args):
    stmt = (
        select(models.Media, func.count(models.MediaComment.id))
        .join(models.MediaComment, models.MediaComment.media_id == models.Media.id)
        .where(models.MediaComment.account_id == account.id)
        .group_by(models.Media.id)
        .order_by(func.count(models.MediaComment.id).desc())
        .limit(args.limit or 10)
    )
    table = Table("Count", "Account", "Media", "Media-Created")
    with db.Session() as session, Live(table, refresh_per_second=4):
        for value, comments in session.execute(stmt).all():
            table.add_row(
                f"{comments:>5}",
                f"[{value.account.id}] {value.account.info_name}",
                f"[{value.id}] {value.info_title}",
                f"{value.created_at}",
            )


def parse_args():
    parser = MetricoArgumentParser("media")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("account", type=int)
    parser.add_argument(
        "mode",
        nargs="?",
        choices=[
            "info",
            "infos",
            "stats",
            "subscriptions",
            "followers",
            "commented",
            "comments",
        ],
        default="info",
        const="info",
    )

    config, args = parser.parse_args()
    return parser, config, args


def main() -> int:
    _, config, args = parse_args()
    db = MetricoDB(config=config)
    account = db.get_account(args.account)
    if account is None:
        return 1
    match args.mode:
        case "infos":
            account_infos(db, account, args)
        case "stats":
            account_stats(db, account, args)
        case "subscriptions":
            account_subscriptions(db, account, args)
        case "followers":
            account_followers(db, account, args)
        case "comments":
            account_comments(db, account, args)
        case "commented":
            account_commented(db, account, args)
        case "info" | _:
            account_info(db, account)
    return 0


if __name__ == "__main__":
    main()
