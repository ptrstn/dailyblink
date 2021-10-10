import pathlib

from bs4 import BeautifulSoup
from mutagen.mp4 import MP4

from dailyblink.settings import BASE_URL, COVER_FILE_NAME


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
    cover_url = soup.find_all("img", {"class": "book-cover__image"})[0]["src"]

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


def get_daily_blink_info(scraper, language="en"):
    daily_blink_url = f"{BASE_URL}/{language}/nc/daily/"
    response = scraper.get(daily_blink_url)
    return _create_blink_info(response.text)


def request_blinkist_book_text(scraper, blink_url):
    response = scraper.get(blink_url)
    soup = BeautifulSoup(response.text, "html.parser")

    book_id = soup.find_all("div", {"class": "reader__container"})[0]["data-book-id"]

    chapter_list_elements = soup.find_all("li", {"class": "chapters"})
    chapter_ids = [
        chapter_element["data-chapterid"]
        for chapter_element in chapter_list_elements
        if "data-chapterid" in chapter_element.attrs
    ]

    chapters = soup.find_all(None, {"class": "chapter chapter"})
    book_text = [chapter.text.strip() for chapter in chapters]

    chapter_texts = [
        (chapter.split("\n", 1)[0], chapter.split("\n", 1)[1]) for chapter in book_text
    ]

    return {"book-id": book_id, "chapter-ids": chapter_ids, "chapters": chapter_texts}


def request_audio(scraper, book_id, chapter_id):
    url = f"{BASE_URL}/api/books/{book_id}/chapters/{chapter_id}/audio"
    headers = {"x-requested-with": "XMLHttpRequest"}
    response = scraper.get(url, headers=headers)
    if response.status_code == 404:  # Text only book, no audio
        raise ValueError(
            f"Audio track does not exist for book {book_id} chapter {chapter_id}"
        )
    audio_url = response.json().get("url")
    return scraper.get(audio_url)


def save_audio_content(audio_response, file_path):
    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as file:
        file.write(audio_response.content)


def save_book_cover(scraper, cover_url, file_path):
    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as file:
        file.write(scraper.get(cover_url).content)


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
