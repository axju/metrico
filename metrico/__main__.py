import sys
from argparse import ArgumentParser
from logging import getLogger

from metrico import __version__

logger = getLogger("metrico")


def main():
    parser = ArgumentParser(prog="metrico", description="Just some metrics stuff", epilog="build by axju")
    parser.add_argument("-V", "--version", action="version", version=__version__)
    parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
