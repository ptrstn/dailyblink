import re
from datetime import date

from dailyblink.core import (
    get_daily_blink_info,
    request_blinkist_book_text,
    save_book_text,
    save_book_cover,
    request_audio,
    save_audio_content,
    set_m4a_meta_data,
)
from dailyblink.settings import BLINKS_PATH, COVER_FILE_NAME, PLAYLIST_FILE_NAME


def main():
    print("Downloading the free daily Blinks...\n")

    languages = {
        "english": "en",
        "german": "de",
    }

    for language, language_code in languages.items():
        blink_info = get_daily_blink_info(language=language_code)
        blink_url = blink_info["url"]

        print(f"{language} ({language_code}):")
        print(f"{blink_info['title']} - {blink_info['author']}\n")

        blink = request_blinkist_book_text(blink_url)
        book_id = blink["book-id"]
        chapter_ids = blink["chapter-ids"]
        chapters = blink["chapters"]

        valid_title = re.sub(r"([^\s\w]|_)+", "", blink_info["title"])
        valid_author = re.sub(r"([^\s\w]|_)+", "", blink_info["author"])
        directory = BLINKS_PATH / language / f"{date.today()} - {valid_title}"

        print("Saving book text...")
        save_book_text(
            blink_info,
            chapters,
            file_path=directory / f"{valid_title} - {valid_author}.md",
        )

        print("Saving book cover...")
        save_book_cover(
            blink_info["cover_url"],
            file_path=directory / COVER_FILE_NAME,
        )

        try:
            file_list = []
            for number, chapter_id in enumerate(chapter_ids):
                print(
                    f"Saving audio track #{number + 1} - {chapters[number][0][:40]}..."
                )
                file_name = f"{number:02d} - {valid_title}.m4a"
                file_path = directory / file_name
                file_list.append(file_name)
                audio_response = request_audio(book_id, chapter_id)
                save_audio_content(audio_response, file_path)
                set_m4a_meta_data(
                    filename=file_path,
                    artist=blink_info["author"],
                    title=chapters[number][0],
                    album=blink_info["title"],
                    track_number=number + 1,
                    total_track_number=len(chapter_ids),
                    genre="Blinkist audiobook",
                )
            with open(directory / PLAYLIST_FILE_NAME, "w") as f:
                print("Creating playlist file...")
                f.write("\n".join(file_list))
        except ValueError:
            print("No audio tracks are available.")

        print()

    print(f"All blinks were saved under {BLINKS_PATH}")


if __name__ == "__main__":
    main()
