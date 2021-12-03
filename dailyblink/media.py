import pathlib

from mutagen.mp4 import MP4


def create_file(content, path, mode):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, mode) as file:
        file.write(content)


def save_media(media, file_path):
    create_file(content=media, path=file_path, mode="wb")


def save_text(text, file_path):
    create_file(content=text, path=file_path, mode="w+")


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
