import pathlib

from mutagen.mp4 import MP4


def save_media(media, file_path):
    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, mode="wb") as file:
        file.write(media)


def save_text(text, file_path):
    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, mode="w+", encoding="utf-8") as file:
        file.write(text)


def set_m4a_meta_data(
    filename,
    artist=None,
    title=None,
    album=None,
    track_number=None,
    total_track_number=None,
    genre=None,
):
    mp4_file = MP4(filename)

    if not mp4_file.tags:
        mp4_file.add_tags()

    tags = mp4_file.tags

    if artist:
        tags["\xa9ART"] = artist
    if title:
        tags["\xa9alb"] = album
    if album:
        tags["\xa9nam"] = title
    if track_number and total_track_number:
        tags["trkn"] = [(track_number, total_track_number)]
    if genre:
        tags["\xa9gen"] = genre
    tags.save(filename)
