from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from typing import Any


GEOCODE_CACHE: dict[str, dict[str, Any]] = {}
GEOCODE_CACHE_TTL_SECONDS = 60 * 60 * 24


def normalize_address(address: str) -> str:
    return " ".join((address or "").strip().split())


def is_vietnam_coord(lat: float, lng: float) -> bool:
    return 8 <= lat <= 24 and 102 <= lng <= 110


def geocode_address(address: str) -> dict[str, Any] | None:
    normalized = normalize_address(address)
    if not normalized:
        return None

    cache_key = normalized.casefold()
    cached = GEOCODE_CACHE.get(cache_key)
    if cached and time.time() - cached["cached_at"] < GEOCODE_CACHE_TTL_SECONDS:
        return cached["result"]

    query = normalized
    if "việt nam" not in normalized.casefold() and "vietnam" not in normalized.casefold():
        query = f"{normalized}, Việt Nam"

    params = urllib.parse.urlencode(
        {
            "format": "jsonv2",
            "q": query,
            "countrycodes": "vn",
            "limit": 1,
            "addressdetails": 1,
        }
    )
    req = urllib.request.Request(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={"User-Agent": "XanhSM-RAG-FoodRecommendation/1.0"},
    )
    with urllib.request.urlopen(req, timeout=6) as response:
        data = json.loads(response.read().decode("utf-8"))

    if not data:
        return None

    first = data[0]
    lat = float(first["lat"])
    lng = float(first["lon"])
    if not is_vietnam_coord(lat, lng):
        return None

    result = {
        "lat": lat,
        "lng": lng,
        "display_name": first.get("display_name") or normalized,
        "source": "nominatim",
    }
    GEOCODE_CACHE[cache_key] = {"cached_at": time.time(), "result": result}
    return result
