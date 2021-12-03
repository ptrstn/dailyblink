import pathlib

from mutagen.mp4 import MP4

from dailyblink.settings import COVER_FILE_NAME


def save_media(media, file_path):
    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as file:
        file.write(media)


def save_book_text(blink_info, chapters, file_path, cover_path=COVER_FILE_NAME):
    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w+") as file:
        file.write(f"# {blink_info['title']}\n\n")
        file.write(f"_{blink_info['author']}_\n\n")
        file.write(f"{blink_info['read_time']}\n\n")
        file.write(f"![cover]({cover_path})\n\n")

        file.write(f"### Synopsis\n\n{blink_info['synopsis']}\n\n")
        file.write(f"### Who is it for?\n\n{blink_info['for_who']}\n\n")
        file.write(f"### About the author\n\n{blink_info['about_author']}\n\n")
        for number, chapter in enumerate(chapters):
            if number != 0 and number != len(chapters) - 1:
                file.write(f"## Blink {number} - {chapter[0]}\n\n")
            else:
                file.write(f"## {chapter[0]}\n\n")

            file.write(f"{chapter[1]}\n\n")

        file.write(f"Source: {blink_info['url']}\n\n")


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
