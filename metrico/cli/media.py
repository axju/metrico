# type: ignore
from rich.live import Live
from rich.table import Table

from metrico.cli.utils import MetricoArgumentParser, to_local_time
from metrico.database import models


def media_info(media: models.Media):
    print(f"ID: {media.id} - Identifier: {media.identifier} - Account: {media.account.info_name} [id={media.account.id}] - Platform: {media.account.platform}")
    print(
        f"  Update:\n    Info:     {media.info_last_update} [{media.info.count()}]\n    Data:     {media.stats_last_update} [{media.stats.count()}]\n    Comments: {media.comments_last_update} [{media.comments.count()}]"
    )

    print(
        f"  Info [{media.info.count()}]:\n    Title:         {media.info[0].title}\n    Caption:       {media.info[0].caption[:120]}\n    Dis. Comments: {media.info[0].disable_comments}"
    )
    print(f"  Stats [{media.stats.count()}]:\n    Comments: {media.stats_comments:>8}\n    Likes:    {media.stats_likes:>8}")


def media_stats(media: models.Media):
    table = Table("ID", "Timestamp", "Comments", "Likes", "Views")
    with Live(table, refresh_per_second=4):
        for value in media.stats.all():
            table.add_row(f"{value.id}", f"{to_local_time(value.timestamp):%Y-%m-%d %H:%M}", f"{value.comments}", f"{value.likes}", f"{value.views}")


def parse_args():
    parser = MetricoArgumentParser("media")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("media", type=int)
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["info", "stats"],
        default="info",
        const="info",
    )

    metrico, args = parser.parse_args()
    return parser, metrico, args


def main() -> int:
    _, metrico, args = parse_args()
    with metrico.db.Session() as session:
        media = metrico.db.get_media(args.media, session=session)
        if media is None:
            return 1
        match args.mode:
            case "stats":
                media_stats(media)
            case _:
                media_info(media)

    return 0


if __name__ == "__main__":
    main()
