import argparse
import pathlib

from dailyblink import __version__
from dailyblink.core import BlinkistScraper
from dailyblink.settings import (
    BLINKS_DEFAULT_PATH,
    BLINKS_DIR_NAME,
)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Tool to download the audio and text "
            "of the free daily book from blinkist.com"
        ),
    )

    parser.add_argument(
        "--version", action="version", version="%(prog)s {}".format(__version__)
    )

    parser.add_argument(
        "-p",
        "--path",
        default=BLINKS_DEFAULT_PATH,
        help=(
            f"Path of where the blinks should be saved. Default: {BLINKS_DEFAULT_PATH}"
        ),
    )

    parser.add_argument(
        "-l",
        "--language",
        nargs="+",
        choices=["en", "de"],
        default=["en", "de"],
        help="Language of the free daily. Default: english german",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    base_path = pathlib.Path(args.path) / BLINKS_DIR_NAME
    blinkist_scraper = BlinkistScraper()
    blinkist_scraper.download_daily_blinks(args.language, base_path)


if __name__ == "__main__":
    main()
