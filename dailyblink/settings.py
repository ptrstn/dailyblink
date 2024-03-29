import pathlib

BASE_URL = "https://www.blinkist.com"

COVER_FILE_NAME_STEM = "cover"
PLAYLIST_FILE_NAME = "playlist.m3u"
BLINKS_DEFAULT_PATH = pathlib.Path.home() / "Musik"
BLINKS_DIR_NAME = "blinks"

LANGUAGES = {
    "en": "english",
    "de": "german",
}

MAX_CLOUDFLARE_ATTEMPTS = 10
CLOUDFLARE_WAIT_TIME = 2

MAX_LINE_LENGTH = 67
