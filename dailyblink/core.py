import pathlib
import re
import time
from datetime import date

import cloudscraper
from bs4 import BeautifulSoup
from cloudscraper import CloudflareChallengeError

from dailyblink.media import (
    set_m4a_meta_data,
    save_media,
    save_text,
)
from dailyblink.settings import (
    BASE_URL,
    COVER_FILE_NAME,
    PLAYLIST_FILE_NAME,
    LANGUAGES,
    MAX_CLOUDFLARE_ATTEMPTS,
    CLOUDFLARE_WAIT_TIME,
)


class BlinkistScraper:
    def __init__(self):
        self._reset_cloudscraper()

    def download_daily_blinks(self, languages: list, base_path: pathlib.Path):
        print("Downloading the free daily Blinks...")
        try:
            self._attempt_daily_blinks_download(languages, base_path)
        except CloudflareChallengeError as e:
            print(e)
            print("Retrying...")
            for index in range(1, MAX_CLOUDFLARE_ATTEMPTS + 1):
                print(f"Attempt {index}/{MAX_CLOUDFLARE_ATTEMPTS}... ", end="")
                time.sleep(CLOUDFLARE_WAIT_TIME)
                self._reset_cloudscraper()
                try:
                    self._attempt_daily_blinks_download(languages, base_path)
                    break
                except CloudflareChallengeError:
                    print("FAILED")

    def _reset_cloudscraper(self):
        self.scraper = cloudscraper.create_scraper()

    def _attempt_daily_blinks_download(self, languages: list, base_path: pathlib.Path):
        for language_code in languages:
            self._download_daily_blinks(language_code, base_path)

        print()
        print(f"All blinks were saved under {base_path.absolute()}")

    def _download_daily_blinks(self, language_code, base_path):
        language = LANGUAGES.get(language_code)
        blink_info = self._get_daily_blink_info(language=language_code)
        blink_url = blink_info["url"]

        print()
        print(f"{language} ({language_code}):")
        print(f"{blink_info['title']} - {blink_info['author']}\n")

        blink = self._request_blinkist_book_text(blink_url=blink_url)
        book_id = blink["book-id"]
        chapter_ids = blink["chapter-ids"]
        chapters = blink["chapters"]

        valid_title = re.sub(r"([^\s\w]|_)+", "", blink_info["title"])
        valid_author = re.sub(r"([^\s\w]|_)+", "", blink_info["author"])
        book_path = base_path / language / f"{date.today()} - {valid_title}"

        print("Saving book text...")
        markdown_text = _create_markdown_text(blink_info, chapters)
        markdown_book_path = book_path / f"{valid_title} - {valid_author}.md"
        save_text(text=markdown_text, file_path=markdown_book_path)

        print("Saving book cover...")
        cover_response = self.scraper.get(blink_info["cover_url"])
        cover = cover_response.content
        cover_path = book_path / COVER_FILE_NAME
        save_media(media=cover, file_path=cover_path)

        try:
            file_list = []
            for number, chapter_id in enumerate(chapter_ids):
                print(
                    f"Saving audio track #{number + 1} - {chapters[number][0][:40]}..."
                )
                file_name = f"{number:02d} - {valid_title}.m4a"
                file_path = book_path / file_name
                file_list.append(file_name)
                audio_response = self._request_audio(
                    book_id=book_id, chapter_id=chapter_id
                )
                save_media(media=audio_response.content, file_path=file_path)
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

    def _get_daily_blink_info(self, language="en"):
        daily_blink_url = f"{BASE_URL}/{language}/nc/daily/"
        response = self.scraper.get(daily_blink_url)
        return _create_blink_info(response.text)

    def _request_blinkist_book_text(self, blink_url):
        response = self.scraper.get(blink_url)
        soup = BeautifulSoup(response.text, "html.parser")

        book_id = soup.find_all("div", {"class": "reader__container"})[0][
            "data-book-id"
        ]

        chapter_list_elements = soup.find_all("li", {"class": "chapters"})
        chapter_ids = [
            chapter_element["data-chapterid"]
            for chapter_element in chapter_list_elements
            if "data-chapterid" in chapter_element.attrs
        ]

        chapters = soup.find_all(None, {"class": "chapter chapter"})
        book_text = [chapter.text.strip() for chapter in chapters]

        chapter_texts = [
            (chapter.split("\n", 1)[0], chapter.split("\n", 1)[1])
            for chapter in book_text
        ]

        return {
            "book-id": book_id,
            "chapter-ids": chapter_ids,
            "chapters": chapter_texts,
        }

    def _request_audio(self, book_id, chapter_id):
        url = f"{BASE_URL}/api/books/{book_id}/chapters/{chapter_id}/audio"
        headers = {"x-requested-with": "XMLHttpRequest"}
        response = self.scraper.get(url, headers=headers)
        if response.status_code == 404:  # Text only book, no audio
            raise ValueError(
                f"Audio track does not exist for book {book_id} chapter {chapter_id}"
            )
        audio_url = response.json().get("url")
        return self.scraper.get(audio_url)


def _create_blink_info(response_text):
    soup = BeautifulSoup(response_text, "html.parser")
    daily_book_href = soup.find_all("a", {"class": "daily-book__cta"})[0]["href"]
    title = soup.find_all(None, {"class": "daily-book__headline"})[0].text.strip()
    author = (
        soup.find_all(None, {"class": "daily-book__author"})[0]
        .text.strip()
        .split(" ", 1)[1]
    )
    read_time = soup.find_all(None, {"class": "book-stats__label"})[0].text.strip()
    synopsis = soup.find_all(None, {"class": "book-tabs__content"})[0].text.strip()
    for_who = soup.find_all(None, {"class": "book-tabs__content"})[1].text.strip()
    about_author = soup.find_all(None, {"class": "book-tabs__content"})[2].text.strip()
    cover_url = soup.find_all("img", {"class": "legacy-book-cover__image"})[0]["src"]

    return {
        "url": BASE_URL + daily_book_href,
        "title": title,
        "author": author,
        "read_time": read_time,
        "synopsis": synopsis,
        "for_who": for_who,
        "about_author": about_author,
        "cover_url": cover_url,
    }


def _create_markdown_text(blink_info, chapters, cover_path=COVER_FILE_NAME):
    markdown_text = f"# {blink_info['title']}\n\n"
    markdown_text += f"_{blink_info['author']}_\n\n"
    markdown_text += f"{blink_info['read_time']}\n\n"
    markdown_text += f"![cover]({cover_path})\n\n"

    markdown_text += f"### Synopsis\n\n{blink_info['synopsis']}\n\n"
    markdown_text += f"### Who is it for?\n\n{blink_info['for_who']}\n\n"
    markdown_text += f"### About the author\n\n{blink_info['about_author']}\n\n"
    for number, chapter in enumerate(chapters):
        if number != 0 and number != len(chapters) - 1:
            markdown_text += f"## Blink {number} - {chapter[0]}\n\n"
        else:
            markdown_text += f"## {chapter[0]}\n\n"

        markdown_text += f"{chapter[1]}\n\n"

    markdown_text += f"Source: {blink_info['url']}\n\n"
    return markdown_text
