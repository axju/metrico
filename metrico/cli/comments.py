# type: ignore
from rich.live import Live
from rich.table import Table

from metrico import MetricoCore
from metrico.cli.utils import MetricoBasicFilterArgumentParser, to_local_time
from metrico.database.query import MediaCommentOrder, MediaCommentQuery


def list_media_comment(metrico: MetricoCore, args):
    table = Table("ID", "Account", "Media", "Media-Account", "Created", "Likes", "Text")
    with Live(table, refresh_per_second=4):
        for comment in metrico.db.iter_query(MediaCommentQuery.from_namespace(args)):
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
    metrico, args = parser.parse_args()
    return parser, metrico, args


def main() -> int:
    _, metrico, args = parse_args()
    list_media_comment(metrico, args)
    return 0


if __name__ == "__main__":
    main()
