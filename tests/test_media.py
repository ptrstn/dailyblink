from dailyblink.media import save_text


def test_save_text():
    text = "CO₂-Emissionen \u2060 \u2082"
    file_path = "test_output/special_characters.md"
    save_text(text=text, file_path=file_path)
