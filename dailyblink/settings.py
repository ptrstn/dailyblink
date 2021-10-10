import pathlib

BASE_URL = "https://www.blinkist.com"

COVER_FILE_NAME = "cover.jpg"
PLAYLIST_FILE_NAME = "playlist.m3u"
BLINKS_DEFAULT_PATH = pathlib.Path.home() / "Musik"
BLINKS_DIR_NAME = "blinks"

AVAILABLE_LANGUAGES = {
    "english": "en",
    "german": "de",
}
