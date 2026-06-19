from __future__ import annotations

import unicodedata


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return strip_accents(value).casefold().strip()


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_marks.replace("đ", "d").replace("Đ", "D")


def split_terms(value: str | None) -> list[str]:
    text = normalize_text(value)
    return [part.strip() for part in text.replace("/", ",").split(",") if part.strip()]
