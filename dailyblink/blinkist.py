import pathlib
import re
import sys
import time
from getpass import getpass
from html import unescape

import requests
import yaml
from bs4 import BeautifulSoup
from mutagen.mp4 import MP4
from requests import HTTPError

BASE_URL = "https://www.blinkist.com"


def get_book_info(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    book_href = soup.findAll("a", {"class": "cta--play"})[0]["href"]

    title = soup.findAll("h1", {"class": "book__header__title"})[0].text.strip()
    subtitle = soup.findAll("h2", {"class": "book__header__subtitle"})[0].text.strip()
    author = (
        soup.findAll("", {"class": "book__header__author"})[0]
        .text.strip()
        .split(" ", 1)[1]
    )
    read_time = soup.findAll("", {"class": "book__header__info-item-body"})[
        0
    ].text.strip()
    synopsis = soup.findAll("div", {"class": "book-tabs-v0__content"})[0].text.strip()
    for_who = soup.findAll("", {"class": "book-tabs-v0__content"})[1].text.strip()
    about_author = soup.findAll("", {"class": "book-tabs-v0__content"})[2].text.strip()
    cover_url = soup.findAll("img", {"class": "hidden-xs"})[0]["src"]

    return {
        "url": BASE_URL + book_href,
        "title": title,
        "subtitle": subtitle,
        "author": author,
        "read_time": read_time,
        "synopsis": synopsis,
        "for_who": for_who,
        "about_author": about_author,
        "cover_url": cover_url,
    }


def login_to_blinkist(username, password, language="en"):
    session = requests.session()
    login_url = f"{BASE_URL}/{language}/nc/login"
    response = session.get(url=login_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_token = soup.find("meta", {"name": "csrf-token"}).attrs["content"]
    response = session.post(
        url=login_url,
        data={
            "login[email]": username,
            "login[password]": password,
            "utf8": unescape("%E2%9C%93"),
            "authenticity_token": csrf_token,
        },
        allow_redirects=True,
    )

    if "Log in to Blinkist" in response.text:
        raise ValueError("Incorrect username/ password")
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code} {response.reason}")
    return session


def request_category_urls(language="en"):
    categories_url = f"{BASE_URL}/{language}/nc/books/"
    response = requests.get(categories_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    return [
        f"{BASE_URL}{a['href']}/books"
        for a in soup.findAll("a", {"class": "category-list__link"})
    ]


def request_book_urls_from_category_url(category_url):
    response = requests.get(category_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    return [a["href"] for a in soup.findAll("a", {"class": "letter-book-list__item"})]


def flatten_book_urls_list(book_urls):
    return sorted(
        set([item for category_items in book_urls for item in category_items])
    )


def request_all_book_urls(language):
    category_urls = request_category_urls(language)

    book_urls = [
        request_book_urls_from_category_url(category_url)
        for category_url in category_urls
    ]

    return flatten_book_urls_list(book_urls)


def request_blinkist_book_text(blink_url, session):
    response = session.get(blink_url)
    response.raise_for_status()

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
        (chapter.split("\n", 1)[0], chapter.split("\n", 1)[1]) for chapter in book_text
    ]

    return {"book-id": book_id, "chapter-ids": chapter_ids, "chapters": chapter_texts}


def request_audio(book_id, chapter_id, session):
    url = f"{BASE_URL}/api/books/{book_id}/chapters/{chapter_id}/audio"
    headers = {"x-requested-with": "XMLHttpRequest"}
    response = session.get(url, headers=headers)
    if response.status_code == 404:  # Text only book, no audio
        raise ValueError(
            f"Audio track does not exist for book {book_id} chapter {chapter_id}"
        )
    response.raise_for_status()
    audio_url = response.json().get("url")

    response = session.get(audio_url)
    response.raise_for_status()
    return response


def save_audio_content(audio_response, file_path):
    # print(f"Saving audio content in {file_path}...")
    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as file:
        file.write(audio_response.content)


def save_book_cover(cover_url, file_path):
    # print(f"Saving book cover in {file_path}...")
    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as file:
        response = requests.get(cover_url)
        try:
            response.raise_for_status()
            file.write(response.content)
        except requests.exceptions.HTTPError:
            print("Cant download book cover")


def save_book_text(blink_info, chapters, file_path):
    # print(f"Saving book text in {file_path}...")
    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w+") as file:
        file.write(f"# {blink_info['title']}\n\n")
        file.write(f"{blink_info['subtitle']}\n\n")
        file.write(f"_{blink_info['author']}_\n\n")
        file.write(f"{blink_info['read_time']}\n\n")
        file.write("![cover](cover.jpg)\n\n")

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
    # print(f"Setting meta data in {filename}...")
    tags = MP4(filename).tags
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


def download_book(session, book_url, base_directory):
    print()
    print(f"Retrieving info for {book_url}...")
    blink_info = get_book_info(book_url)
    blink_url = blink_info["url"]

    print(f"{blink_info['title']} - {blink_info['author']}\n")

    blink = request_blinkist_book_text(blink_url, session)
    book_id = blink["book-id"]
    chapter_ids = blink["chapter-ids"]
    chapters = blink["chapters"]

    valid_title = re.sub(r"([^\s\w]|_)+", "", blink_info["title"])
    valid_author = re.sub(r"([^\s\w]|_)+", "", blink_info["author"])
    directory = f"{base_directory}/{valid_title}"

    print("Saving book text...")
    save_book_text(
        blink_info,
        chapters,
        file_path=f"{directory}/{valid_title} - {valid_author}.md",
    )

    save_book_cover(
        blink_info["cover_url"], file_path=f"{directory}/cover.jpg",
    )

    try:
        for number, chapter_id in enumerate(chapter_ids):
            print(f"Saving audio track #{number + 1} - {chapters[number][0][:40]}...")
            file_path = f"{directory}/{number:02d} - {valid_title}.m4a"
            audio_response = request_audio(book_id, chapter_id, session)
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
    except ValueError:
        print("No audio tracks are available.")

    return valid_author, valid_title


def open_completed_urls():
    pass


def main():
    language = "de"
    print("requesting all book urls...")
    book_urls = request_all_book_urls(language=language)

    print("Logging in into blinkist...")
    username = input("Username: ")
    password = getpass()
    try:
        session = login_to_blinkist(username, password)
    except HTTPError as e:
        # TODO find bypass for reCAPTCHA login
        print(e)
        sys.exit(0)

    base_directory = pathlib.Path(pathlib.Path.home(), "Musik", "all_blinks")
    pathlib.Path(base_directory, "downloaded_urls.yml")

    with open("downloaded_urls.yml", "r+") as outfile:
        already_downloaded_urls = yaml.load(outfile, Loader=yaml.FullLoader)

    # book_urls = book_urls[2654:len(book_urls)]
    book_urls = sorted(set(book_urls) - set(already_downloaded_urls))
    for book_url in book_urls:
        try:
            download_book(session, book_url, base_directory)
        except requests.exceptions.HTTPError as e:
            print()
            print(f"Error trying to download {book_url}")
            print(e)
            print("Waiting 60 seconds and trying again...")
            time.sleep(60)
            try:
                download_book(session, book_url, base_directory)
            except:
                print()
                print(f"Error trying to download {book_url}")
                print(e)
                print("Waiting 5 Minutes and trying again...")
                time.sleep(300)
                try:
                    download_book(session, book_url, base_directory)
                except:
                    print("Another Error....")
                    print("Waiting 15 minutes and renewing session...")
                    time.sleep(900)
                    session = login_to_blinkist(username, password)
                    print("Got new session")
                    print("Getting the book.")
                    download_book(session, book_url, base_directory)
        with open("downloaded_urls.yml", "a+") as outfile:
            yaml.dump([book_url], outfile, indent=2)

        # TODO save book_url in a file like completed.txt
