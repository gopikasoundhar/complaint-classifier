"""Text cleaning utilities."""
import re
import unicodedata

import pandas as pd


def clean_text(text) -> str:
    """Lowercase, strip punctuation/symbols, collapse whitespace.

    Punctuation is removed by Unicode category (P* and S*) instead of a regex of
    ASCII symbols, so non-English letters (e.g. Tamil) and their combining marks
    are preserved.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = "".join(" " if unicodedata.category(ch)[0] in ("P", "S") else ch for ch in text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_dataframe(df: pd.DataFrame, keep: str = "first") -> pd.DataFrame:
    """Clean the text column, then drop empty and duplicate rows.

    keep="last" lets later rows (admin corrections) win over earlier duplicates.
    """
    df = df.copy()
    df = df.dropna(subset=["text", "category"])
    df["text"] = df["text"].astype(str).map(clean_text)
    df["category"] = df["category"].astype(str).str.strip()
    df = df[(df["text"] != "") & (df["category"] != "")]
    df = df.drop_duplicates(subset="text", keep=keep)
    return df.reset_index(drop=True)
