from __future__ import annotations

import unicodedata
import re


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.casefold())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def classify_intent(query: str, persona: str = "customer") -> str:
    normalized = query.casefold()
    folded = _fold(query)
    if any(term in normalized for term in ("ăn", "món", "quán", "food", "đói")) or re.search(r"\b(mon|quan|food|doi|com|pho|bun|banh mi)\b", folded):
        return "food_recommendation"
    if any(term in normalized for term in ("đặt xe", "gọi xe", "cuốc", "trip", "tài xế")) or any(
        term in folded for term in ("dat xe", "goi xe", "book xe", "cuoc", "trip", "tai xe")
    ):
        return "ride_support"
    if (" tu " in f" {folded} " and any(term in f" {folded} " for term in (" den ", " toi ", " ve "))) and any(
        term in folded for term in ("xe", "vinhomes", "san bay", "ben thanh")
    ):
        return "ride_support"
    if persona == "merchant":
        return "merchant_analytics"
    if persona == "operator":
        return "operations_monitoring"
    if persona == "executive":
        return "executive_insight"
    if persona == "driver":
        return "driver_support"
    return "rag"
