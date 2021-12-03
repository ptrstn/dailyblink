import pathlib

from dailyblink.core import (
    save_media,
    BlinkistScraper,
    _create_markdown_text,
)
from dailyblink.media import save_text

blinkist_scraper = BlinkistScraper()


def test_download_daily_blinks():
    blinkist_scraper.download_daily_blinks(["de", "en"], pathlib.Path(".") / "blinks")


def test_get_daily_blink_url():
    en_url = blinkist_scraper._get_daily_blink_info(language="en")["url"]
    assert "https://www.blinkist.com/en/nc/daily/reader/" in en_url
    de_url = blinkist_scraper._get_daily_blink_info(language="de")["url"]
    assert "https://www.blinkist.com/de/nc/daily/reader/" in de_url


def test_get_book_id():
    blink_url = blinkist_scraper._get_daily_blink_info()["url"]
    book = blinkist_scraper._request_blinkist_book_text(blink_url=blink_url)
    book_id = book["book-id"]
    assert len(book_id) == 24, "ID is 24 characters"


def test_get_chapter_ids():
    blink_url = blinkist_scraper._get_daily_blink_info()["url"]
    book = blinkist_scraper._request_blinkist_book_text(blink_url=blink_url)
    chapter_ids = book["chapter-ids"]
    assert len(chapter_ids) > 1, "At least one chapter"
    assert len(chapter_ids[0]) == 24, "ID is 24 characters"


def test_request_audio():
    blink_url = blinkist_scraper._get_daily_blink_info(language="de")["url"]
    blink = blinkist_scraper._request_blinkist_book_text(blink_url=blink_url)
    book_id = blink["book-id"]
    chapter_ids = blink["chapter-ids"]

    try:
        track_00 = blinkist_scraper._request_audio(book_id, chapter_ids[0]).content
        track_01 = blinkist_scraper._request_audio(book_id, chapter_ids[1]).content
        track_02 = blinkist_scraper._request_audio(book_id, chapter_ids[2]).content

        save_media(track_00, file_path="test_output/track_00.m4a")
        save_media(track_01, file_path="test_output/track_01.m4a")
        save_media(track_02, file_path="test_output/track_02.m4a")
    except ValueError as e:
        print(e)


def test_request_meta_data():
    meta_data = blinkist_scraper._get_daily_blink_info(language="de")
    assert "title" in meta_data
    assert "author" in meta_data
    assert "synopsis" in meta_data
    assert "for_who" in meta_data
    assert "about_author" in meta_data


def test_request_book_text():
    blink_url = blinkist_scraper._get_daily_blink_info(language="de")["url"]
    chapters = blinkist_scraper._request_blinkist_book_text(blink_url)["chapters"]
    assert len(chapters) > 1, "At least one chapter"


def test_save_book_text():
    blink_info = blinkist_scraper._get_daily_blink_info(language="de")
    blink_url = blink_info["url"]
    chapters = blinkist_scraper._request_blinkist_book_text(blink_url)["chapters"]
    markdown_text = _create_markdown_text(blink_info, chapters)
    save_text(markdown_text, file_path="test_output/daily_blink.md")
