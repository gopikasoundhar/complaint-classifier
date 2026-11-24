import pandas as pd

from app.preprocess import clean_dataframe, clean_text


def test_lowercase_and_punctuation():
    assert clean_text("  NO Water!!!  In   my street... ") == "no water in my street"


def test_empty_and_non_string():
    assert clean_text("") == ""
    assert clean_text("   ") == ""
    assert clean_text(None) == ""
    assert clean_text(123) == ""


def test_only_symbols():
    assert clean_text("@#$%^&*()!!!") == ""


def test_non_english_letters_kept():
    assert clean_text("குடிநீர் வரவில்லை!") == "குடிநீர் வரவில்லை"


def test_dataframe_drops_empty_and_duplicates():
    df = pd.DataFrame({
        "text": ["No water!", "no water", "   ", None, "Pothole on road"],
        "category": ["Water Supply", "Water Supply", "Roads", "Roads", "Roads"],
    })
    out = clean_dataframe(df)
    assert list(out["text"]) == ["no water", "pothole on road"]
