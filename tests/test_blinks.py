from dailyblink.blinks import (
    get_daily_blink_info,
    request_blinkist_book,
    request_audio,
    save_audio_content,
    save_book_text,
    main,
)


def test_get_daily_blink_url():
    en_url = get_daily_blink_info(language="en")["url"]
    assert "https://www.blinkist.com/en/nc/daily/reader/" in en_url
    de_url = get_daily_blink_info(language="de")["url"]
    assert "https://www.blinkist.com/de/nc/daily/reader/" in de_url


def test_get_book_id():
    blink_url = get_daily_blink_info()["url"]
    book_id = request_blinkist_book(blink_url)["book-id"]
    assert len(book_id) == 24, "ID is 24 characters"


def test_get_chapter_ids():
    blink_url = get_daily_blink_info()["url"]
    chapter_ids = request_blinkist_book(blink_url)["chapter-ids"]
    assert len(chapter_ids) > 1, "At least one chapter"
    assert len(chapter_ids[0]) == 24, "ID is 24 characters"


def test_request_audio():
    blink_url = get_daily_blink_info(language="de")["url"]
    blink = request_blinkist_book(blink_url)
    book_id = blink["book-id"]
    chapter_ids = blink["chapter-ids"]

    track_00 = request_audio(book_id, chapter_ids[0])
    track_01 = request_audio(book_id, chapter_ids[1])
    track_02 = request_audio(book_id, chapter_ids[2])

    save_audio_content(track_00, file_path="test_output/track_00.m4a")
    save_audio_content(track_01, file_path="test_output/track_01.m4a")
    save_audio_content(track_02, file_path="test_output/track_02.m4a")


def test_request_meta_data():
    meta_data = get_daily_blink_info(language="de")
    assert "title" in meta_data
    assert "author" in meta_data
    assert "synopsis" in meta_data
    assert "for_who" in meta_data
    assert "about_author" in meta_data


def test_request_book_text():
    blink_url = get_daily_blink_info(language="de")["url"]
    book_text = request_blinkist_book(blink_url)["book_text"]
    assert len(book_text) > 1, "At least one chapter"


def test_save_book_text():
    blink_info = get_daily_blink_info(language="de")
    blink_url = blink_info["url"]
    book_text = request_blinkist_book(blink_url)["book_text"]
    save_book_text(blink_info, book_text, file_path="test_output/daily_blink.md")


def test_main():
    main()
