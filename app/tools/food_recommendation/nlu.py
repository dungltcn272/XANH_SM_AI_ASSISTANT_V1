from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


FOOD_TERMS = [
    "ăn", "món", "đồ ăn", "đồ uống", "bữa", "ăn sáng", "ăn trưa", "ăn tối", "ăn khuya",
    "cơm", "bún", "phở", "mì", "miến", "hủ tiếu", "bánh mì", "cháo", "lẩu", "sushi",
    "pizza", "burger", "gà rán", "trà sữa", "cà phê", "cafe", "healthy", "đồ chay",
    "quán", "nhà hàng", "shopeefood", "gợi ý ăn", "recommend food",
]

CATEGORY_TERMS = [
    "cơm", "bún", "phở", "mì", "miến", "hủ tiếu", "bánh mì", "cháo", "lẩu", "sushi",
    "pizza", "burger", "gà rán", "trà sữa", "cà phê", "cafe", "healthy", "đồ chay",
    "đồ uống", "bánh kem", "tráng miệng",
]

TASTE_TERMS = [
    "cay", "ít dầu", "ít ngọt", "ngọt", "mặn", "thanh nhẹ", "no lâu", "healthy",
    "chay", "nhiều rau", "ít béo", "nóng", "lạnh",
]

MEAL_TIME_TERMS = {
    "sáng": ["sáng", "breakfast"],
    "trưa": ["trưa", "lunch"],
    "tối": ["tối", "dinner"],
    "khuya": ["khuya", "đêm", "late"],
}


@dataclass
class FoodSlots:
    is_food_intent: bool = False
    lat: float | None = None
    lng: float | None = None
    category: str | None = None
    taste_tags: list[str] = field(default_factory=list)
    budget_min: int | None = None
    budget_max: int | None = None
    meal_time: str | None = None
    max_distance_km: float = 6


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFD", value)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_marks.replace("đ", "d").replace("Đ", "D").casefold()


def detect_food_intent(text: str) -> bool:
    q = normalize_text(text)
    return any(normalize_text(term) in q for term in FOOD_TERMS)


def extract_food_slots(text: str, chat_history: list[dict] | None = None) -> FoodSlots:
    source = text or ""
    if chat_history:
        # Allow user to send coordinates in the next turn after the bot asks for location.
        recent = "\n".join(turn.get("content", "") for turn in chat_history[-4:] if isinstance(turn, dict))
        if detect_food_intent(recent):
            source = f"{recent}\n{source}"

    slots = FoodSlots(is_food_intent=detect_food_intent(source))
    if not slots.is_food_intent:
        return slots

    slots.lat, slots.lng = extract_lat_lng(source)
    slots.budget_min, slots.budget_max = extract_budget(source)
    slots.category = extract_category(source)
    slots.taste_tags = extract_taste_tags(source)
    slots.meal_time = extract_meal_time(source)
    slots.max_distance_km = extract_distance(source) or slots.max_distance_km
    return slots


def extract_lat_lng(text: str) -> tuple[float | None, float | None]:
    patterns = [
        r"lat\s*[:=]\s*(-?\d+(?:\.\d+)?)\s*[,;\s]+(?:lng|lon|long|longitude)\s*[:=]\s*(-?\d+(?:\.\d+)?)",
        r"(-?\d{1,2}\.\d{3,})\s*[,;]\s*(-?\d{1,3}\.\d{3,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        first = float(match.group(1))
        second = float(match.group(2))
        if is_valid_vietnam_coord(first, second):
            return first, second
        if is_valid_vietnam_coord(second, first):
            return second, first
    return None, None


def is_valid_vietnam_coord(lat: float, lng: float) -> bool:
    return 8 <= lat <= 24 and 102 <= lng <= 110


def extract_budget(text: str) -> tuple[int | None, int | None]:
    q = normalize_text(text)
    max_budget = None
    min_budget = None
    budget_context = any(word in q for word in ["duoi", "toi da", "khong qua", "ngan sach", "budget", "tam", "gia"])
    for match in re.finditer(r"(?<![\d.])(\d{1,3})(?:\s?-\s?(\d{1,3}))?\s*(k|nghin|ngan|000|vnd|đ|dong)?(?![\d.])", q):
        first = int(match.group(1))
        second = int(match.group(2)) if match.group(2) else None
        unit = match.group(3) or ""
        if not unit and not budget_context:
            continue
        if first < 10 and unit not in {"k", "nghin", "ngan", "000"}:
            continue
        first_value = first * 1000 if first < 1000 else first
        if second:
            second_value = second * 1000 if second < 1000 else second
            min_budget = min(first_value, second_value)
            max_budget = max(first_value, second_value)
        elif any(word in q for word in ["duoi", "toi da", "khong qua", "<=", "budget", "tam"]):
            max_budget = first_value
        elif max_budget is None:
            max_budget = first_value
    return min_budget, max_budget


def extract_category(text: str) -> str | None:
    q = normalize_text(text)
    for term in CATEGORY_TERMS:
        if normalize_text(term) in q:
            return term
    return None


def extract_taste_tags(text: str) -> list[str]:
    q = normalize_text(text)
    return [term for term in TASTE_TERMS if normalize_text(term) in q]


def extract_meal_time(text: str) -> str | None:
    q = normalize_text(text)
    for meal_time, terms in MEAL_TIME_TERMS.items():
        if any(normalize_text(term) in q for term in terms):
            return meal_time
    return None


def extract_distance(text: str) -> float | None:
    q = normalize_text(text)
    match = re.search(r"(\d+(?:\.\d+)?)\s*(km|cay so|cây số)", q)
    if not match:
        return None
    return max(1.0, min(float(match.group(1)), 25.0))
