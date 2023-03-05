import sys
from argparse import REMAINDER, SUPPRESS, ArgumentParser
from subprocess import Popen  # nosec

from metrico import __version__


def main():
    parser = ArgumentParser(prog="metrico", description="Just some metrics stuff", epilog="build by axju")
    parser.add_argument("-V", "--version", action="version", version=__version__)
    parser.add_argument(
        "cmd",
        nargs="?",
        choices=["accounts", "account", "medias", "media", "comments", "tools"],
        help="select one command",
    )
    parser.add_argument("args", help=SUPPRESS, nargs=REMAINDER)
    args = parser.parse_args()

    if args.cmd:
        with Popen(f"{sys.executable} -m metrico.cli.{args.cmd} " + " ".join(args.args), shell=True) as proces:  # nosec
            sys.exit(proces.wait())
    parser.print_help()
    sys.exit(0)
