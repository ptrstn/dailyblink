import pathlib

from dailyblink.settings import AVAILABLE_LANGUAGES
from dailyblink.utils import download_blinks
from tests.test_core import scraper


def test_download_blinks():
    download_blinks(scraper, AVAILABLE_LANGUAGES, pathlib.Path(".") / "blinks")
