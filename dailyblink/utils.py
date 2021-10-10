import re
from datetime import date

from dailyblink.core import (
    set_m4a_meta_data,
    save_audio_content,
    request_audio,
    save_book_cover,
    save_book_text,
    request_blinkist_book_text,
    get_daily_blink_info,
)
from dailyblink.settings import PLAYLIST_FILE_NAME, COVER_FILE_NAME


def download_blinks(scraper, languages, base_path):
    for language, language_code in languages.items():
        blink_info = get_daily_blink_info(scraper=scraper, language=language_code)
        blink_url = blink_info["url"]

        print()
        print(f"{language} ({language_code}):")
        print(f"{blink_info['title']} - {blink_info['author']}\n")

        blink = request_blinkist_book_text(scraper=scraper, blink_url=blink_url)
        book_id = blink["book-id"]
        chapter_ids = blink["chapter-ids"]
        chapters = blink["chapters"]

        valid_title = re.sub(r"([^\s\w]|_)+", "", blink_info["title"])
        valid_author = re.sub(r"([^\s\w]|_)+", "", blink_info["author"])
        book_path = base_path / language / f"{date.today()} - {valid_title}"

        print("Saving book text...")
        save_book_text(
            blink_info=blink_info,
            chapters=chapters,
            file_path=book_path / f"{valid_title} - {valid_author}.md",
        )

        print("Saving book cover...")
        save_book_cover(
            scraper=scraper,
            cover_url=blink_info["cover_url"],
            file_path=book_path / COVER_FILE_NAME,
        )

        try:
            file_list = []
            for number, chapter_id in enumerate(chapter_ids):
                print(
                    f"Saving audio track #{number + 1} - {chapters[number][0][:40]}..."
                )
                file_name = f"{number:02d} - {valid_title}.m4a"
                file_path = book_path / file_name
                file_list.append(file_name)
                audio_response = request_audio(
                    scraper=scraper, book_id=book_id, chapter_id=chapter_id
                )
                save_audio_content(audio_response=audio_response, file_path=file_path)
                set_m4a_meta_data(
                    filename=file_path,
                    artist=blink_info["author"],
                    title=chapters[number][0],
                    album=blink_info["title"],
                    track_number=number + 1,
                    total_track_number=len(chapter_ids),
                    genre="Blinkist audiobook",
                )
            with open(book_path / PLAYLIST_FILE_NAME, "w") as f:
                print("Creating playlist file...")
                f.write("\n".join(file_list))
        except ValueError:
            print("No audio tracks are available.")

        print()

    print(f"All blinks were saved under {base_path.absolute()}")
