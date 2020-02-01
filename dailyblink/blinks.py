import pathlib
import re
from datetime import date

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.blinkist.com"


def _create_blink_info(response_text):
    soup = BeautifulSoup(response_text, "html.parser")

    daily_book_href = soup.findAll("a", {"class": "daily-book__cta"})[0]["href"]
    title = soup.findAll("", {"class": "daily-book__headline"})[0].text.strip()
    author = soup.findAll("", {"class": "daily-book__author"})[0].text.strip().split(' ', 1)[1]
    read_time = soup.findAll("", {"class": "book-stats__label"})[0].text.strip()
    synopsis = soup.findAll("", {"class": "book-tabs__content"})[0].text.strip()
    for_who = soup.findAll("", {"class": "book-tabs__content"})[1].text.strip()
    about_author = soup.findAll("", {"class": "book-tabs__content"})[2].text.strip()

    return {
        "url": BASE_URL + daily_book_href,
        "title": title,
        "author": author,
        "read_time": read_time,
        "synopsis": synopsis,
        "for_who": for_who,
        "about_author": about_author,
    }


def get_daily_blink_info(language="en"):
    daily_blink_url = f"{BASE_URL}/{language}/nc/daily/"
    response = requests.get(daily_blink_url)
    return _create_blink_info(response.text)


def request_blinkist_book_text(blink_url):
    response = requests.get(blink_url)
    soup = BeautifulSoup(response.text, "html.parser")

    book_id = soup.findAll("div", {"class": "reader__container"})[0]["data-book-id"]

    chapter_list_elements = soup.findAll("li", {"class": "chapters"})
    chapter_ids = [
        chapter_element["data-chapterid"]
        for chapter_element in chapter_list_elements
        if "data-chapterid" in chapter_element.attrs
    ]

    chapters = soup.findAll("", {"class": "chapter chapter"})
    book_text = [chapter.text.strip() for chapter in chapters]

    chapter_texts = [
        (chapter.split('\n', 1)[0], chapter.split('\n', 1)[1])
        for chapter in book_text
    ]

    return {"book-id": book_id, "chapter-ids": chapter_ids, "chapters": chapter_texts}


def request_audio(book_id, chapter_id):
    url = f"{BASE_URL}/api/books/{book_id}/chapters/{chapter_id}/audio"
    headers = {"x-requested-with": "XMLHttpRequest"}
    response = requests.get(url, headers=headers)
    if response.status_code == 404:  # Text only book, no audio
        raise ValueError(
            f"Audio track does not exist for book {book_id} chapter {chapter_id}"
        )
    audio_url = response.json().get("url")
    return requests.get(audio_url)


def save_audio_content(audio_response, file_path):
    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as file:
        file.write(audio_response.content)


def save_book_text(blink_info, chapters, file_path):
    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w+") as file:
        file.write(f"# {blink_info['title']} \n\n")
        file.write(f"_{blink_info['author']}_ \n\n")
        file.write(f"{blink_info['read_time']} \n\n")
        file.write(f"{blink_info['url']} \n\n")
        file.write(f"### Synopsis\n\n{blink_info['synopsis']}\n\n")
        file.write(f"### Who is it for?\n\n{blink_info['for_who']}\n\n")
        file.write(f"### About the author\n\n{blink_info['about_author']}\n\n")
        for number, chapter in enumerate(chapters):
            file.write(f"## Blink {number} - {chapter[0]} \n\n")
            file.write(f"{chapter[1]}\n\n")


def main():
    print("Downloading the free daily Blinks...\n")

    languages = {
        "english": "en",
        "german": "de",
    }

    base_directory = pathlib.Path(pathlib.Path.home(), "Musik", "blinks")

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
        directory = f"{base_directory}/{language}/{date.today()} - {valid_title}"

        print("Saving book text...")
        save_book_text(
            blink_info,
            chapters,
            file_path=f"{directory}/{valid_title} {valid_author}.md",
        )

        try:
            for number, chapter_id in enumerate(chapter_ids):
                print(f"Saving audio track from Blink #{number} - {chapters[number][0][:50]}...")
                file_path = f"{directory}/{number:02d} - {valid_title}.m4a"
                audio_response = request_audio(book_id, chapter_id)
                save_audio_content(audio_response, file_path)
        except ValueError:
            print("No audio tracks are available.")

        print()

    print(f"All blinks were saved under {base_directory}")


if __name__ == "__main__":
    main()
