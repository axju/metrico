from argparse import ArgumentParser
from datetime import datetime

from dateutil import tz
from rich.console import Console

from metrico import MetricoConfig
from metrico.database.query import AccountOrder, MediaCommentOrder, MediaOrder
from metrico.schemas import ModelStatus
from metrico.utils.misc import config_logger

console = Console()

TIME_ZONE = tz.gettz("Europe/Berlin")
TIME_ZONE_UTC = tz.gettz("UTC")


def to_local_time(value: datetime):
    return value.replace(tzinfo=TIME_ZONE_UTC).astimezone(TIME_ZONE)


def find_index(stats, delta: int):
    if stats.count() < 2:
        return 0
    dt_index = 1
    dt_best = stats[0].timestamp - stats[dt_index].timestamp
    dt_error = abs((delta * 3600) - dt_best.total_seconds())
    for current_index in range(2, stats.count()):
        current_dt = stats[0].timestamp - stats[current_index].timestamp
        current_error = abs((delta * 3600) - current_dt.total_seconds())
        if current_error < dt_error:
            dt_index, dt_best, dt_error = current_index, current_dt, current_error
    return dt_index


class MetricoArgumentParserOld(ArgumentParser):
    def __init__(self, prog):
        super().__init__(prog=f"metrico {prog}", epilog="build by axju")

    def add_subparsers(self, **kwargs):
        kwargs["parser_class"] = ArgumentParser
        return super().add_subparsers(**kwargs)

    def parse_args(self, *argv: str):  # type: ignore
        return super().parse_args(args=argv)


class MetricoArgumentParser(ArgumentParser):
    def __init__(self, prog):
        super().__init__(prog=f"metrico {prog}", epilog="build by axju")
        self.add_argument(
            "-v",
            "--verbose",
            action="count",
            help="verbose level... repeat up to three times",
        )
        self.add_argument("-c", "--config", help="set the config file, default=./metrico.toml")

    def add_subparsers(self, **kwargs):
        kwargs["parser_class"] = ArgumentParser
        return super().add_subparsers(**kwargs)

    # pylint: disable=arguments-differ
    def parse_args(self, argv: str | None = None):  # type: ignore
        args = super().parse_args(args=argv)
        if args.verbose:
            config_logger(args.verbose, name="metrico")
        config: MetricoConfig = MetricoConfig.load(path=args.config) if args.config else MetricoConfig.default()
        return config, args


class MetricoBasicFilterArgumentParser(MetricoArgumentParser):
    def __init__(self, prog):
        super().__init__(prog)
        self.add_argument("--limit", type=int)
        self.add_argument("--offset", type=int)
        self.add_argument("--order_asc", action="store_true")
        self.add_argument("--filter_status", type=lambda x: ModelStatus[x], choices=list(ModelStatus))
        self.add_argument("--filter_datetime", nargs=2, type=lambda s: datetime.strptime(s, "%Y-%m-%d"))
        self.add_argument("--filter_account", nargs="*", type=str)
        self.add_argument("--filter_account_id", nargs="*", type=int)


# def basic_filter_arguments(parser):
#     parser.add_argument("--limit", type=int, default=20)
#     parser.add_argument("--offset", type=int)
#     parser.add_argument("--order_asc", action="store_true")
#     parser.add_argument("--filter_status", type=lambda x: ModelStatus[x], choices=list(ModelStatus))
#     parser.add_argument("--filter_datetime", nargs=2, type=lambda s: datetime.strptime(s, "%Y-%m-%d"))
#     parser.add_argument("--filter_account", nargs="*", type=str)
#     parser.add_argument("--filter_account_id", nargs="*", type=int)
#     return parser
#
#
# def parser_add_argument_account_filter(parser):
#     parser = basic_filter_arguments(parser)
#     parser.add_argument("--order_by", type=lambda x: AccountOrder[x], choices=list(AccountOrder))
#     parser.add_argument("--filter_stats_null", action="store_true")
#     parser.add_argument("--filter_stats_views_null", action="store_true")
#     parser.add_argument("--filter_comment_media_id", nargs="*", type=int)
#     parser.add_argument("--filter_comment_media_account_id", nargs="*", type=int)
#     return parser
#
#
# def parser_add_argument_media_filter(parser):
#     parser = basic_filter_arguments(parser)
#     parser.add_argument("--order_by", type=lambda x: MediaOrder[x], choices=list(MediaOrder))
#     return parser
#
#
# def parser_add_argument_media_comment_filter(parser):
#     parser = basic_filter_arguments(parser)
#     parser.add_argument(
#         "--order_by",
#         type=lambda x: MediaCommentOrder[x],
#         choices=list(MediaCommentOrder),
#     )
#     parser.add_argument("--filter_media_account_id", nargs="*", type=int)
#     return parser
