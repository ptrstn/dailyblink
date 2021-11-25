import argparse
import pathlib
import time

import cloudscraper
from cloudscraper import CloudflareChallengeError

from dailyblink import __version__
from dailyblink.settings import (
    AVAILABLE_LANGUAGES,
    BLINKS_DEFAULT_PATH,
    BLINKS_DIR_NAME,
    MAX_CLOUDFLARE_ATTEMPTS,
    CLOUDFLARE_WAIT_TIME,
)
from dailyblink.utils import download_blinks


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Tool to download the audio and text of the free daily book from"
            " blinkist.com"
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
    print("Downloading the free daily Blinks...\n")

    languages = {
        key: value
        for key, value in AVAILABLE_LANGUAGES.items()
        if value in args.language
    }

    base_path = pathlib.Path(args.path) / BLINKS_DIR_NAME
    scraper = cloudscraper.create_scraper()

    try:
        download_blinks(scraper, languages, base_path)
    except CloudflareChallengeError as e:
        print(e)
        print("Retrying...")
        for index in range(1, MAX_CLOUDFLARE_ATTEMPTS + 1):
            print(f"Attempt {index}/{MAX_CLOUDFLARE_ATTEMPTS}... ", end="")
            time.sleep(CLOUDFLARE_WAIT_TIME)
            scraper = cloudscraper.create_scraper()
            try:
                download_blinks(scraper, languages, base_path)
                break
            except CloudflareChallengeError:
                print("FAILED")


if __name__ == "__main__":
    main()
