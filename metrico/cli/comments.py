# type: ignore
from rich.live import Live
from rich.table import Table

from metrico import MetricoDB
from metrico.cli.utils import MetricoBasicFilterArgumentParser, to_local_time
from metrico.database.query import MediaCommentOrder, MediaCommentQuery


def list_media_comment(db: MetricoDB, args):
    table = Table("ID", "Account", "Media", "Media-Account", "Created", "Likes", "Text")
    with Live(table, refresh_per_second=4):
        for comment in db.iter_query(MediaCommentQuery.from_namespace(args)):
            table.add_row(
                f"{comment.id:>7}",
                f"[{comment.account_id}] {comment.account.info_name[:32]}",
                f"[{comment.media_id}] {comment.media.info_title[:32]}",
                f"[{comment.media.account_id}] {comment.media.account.info_name[:32]}",
                f"{to_local_time(comment.created_at):%Y-%m-%d %H:%M}",
                f"{comment.likes}",
                f"{comment.text[:100]}",
            )


def parse_args():
    parser = MetricoBasicFilterArgumentParser("comments")
    parser.add_argument("--order_by", type=lambda x: MediaCommentOrder[x], choices=list(MediaCommentOrder))
    config, args = parser.parse_args()
    return parser, config, args


def main() -> int:
    _, config, args = parse_args()
    db = MetricoDB(config=config)
    list_media_comment(db, args)
    return 0


if __name__ == "__main__":
    main()
