from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from typing import Any


GEOCODE_CACHE: dict[str, dict[str, Any]] = {}
GEOCODE_CACHE_TTL_SECONDS = 60 * 60 * 24
USER_AGENT = "XanhSM-RAG-FoodRecommendation/1.0"


def normalize_address(address: str) -> str:
    return " ".join((address or "").strip().split())


def is_vietnam_coord(lat: float, lng: float) -> bool:
    return 8 <= lat <= 24 and 102 <= lng <= 110


def ensure_vietnam_suffix(address: str) -> str:
    folded = address.casefold()
    if "việt nam" in folded or "viet nam" in folded or "vietnam" in folded:
        return address
    return f"{address}, Vietnam"


def geocode_address(address: str) -> dict[str, Any] | None:
    normalized = normalize_address(address)
    if not normalized:
        return None

    cache_key = normalized.casefold()
    cached = GEOCODE_CACHE.get(cache_key)
    if cached and time.time() - cached["cached_at"] < GEOCODE_CACHE_TTL_SECONDS:
        return cached["result"]

    # Free-first providers. Nominatim is stricter and more stable; Photon is a
    # useful fallback for fuzzy street/alley queries.
    result = geocode_address_nominatim(normalized)
    if result is None:
        result = geocode_address_photon(normalized)

    if result:
        GEOCODE_CACHE[cache_key] = {"cached_at": time.time(), "result": result}
    return result


def geocode_address_nominatim(normalized: str) -> dict[str, Any] | None:
    query = ensure_vietnam_suffix(normalized)
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
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=7) as response:
        data = json.loads(response.read().decode("utf-8"))

    if not data:
        return None

    first = data[0]
    lat = float(first["lat"])
    lng = float(first["lon"])
    if not is_vietnam_coord(lat, lng):
        return None

    return {
        "lat": lat,
        "lng": lng,
        "display_name": first.get("display_name") or normalized,
        "source": "nominatim",
    }


def geocode_address_photon(normalized: str) -> dict[str, Any] | None:
    query = ensure_vietnam_suffix(normalized)
    params = urllib.parse.urlencode({"q": query, "limit": 1, "lang": "vi"})
    req = urllib.request.Request(
        f"https://photon.komoot.io/api/?{params}",
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=7) as response:
        data = json.loads(response.read().decode("utf-8"))

    features = data.get("features") or []
    if not features:
        return None

    feature = features[0]
    coords = feature.get("geometry", {}).get("coordinates") or []
    if len(coords) < 2:
        return None

    lng = float(coords[0])
    lat = float(coords[1])
    if not is_vietnam_coord(lat, lng):
        return None

    props = feature.get("properties") or {}
    display_parts = [
        props.get("name"),
        props.get("street"),
        props.get("district"),
        props.get("city"),
        props.get("state"),
        props.get("country"),
    ]
    display_name = ", ".join(str(part) for part in display_parts if part) or normalized
    return {
        "lat": lat,
        "lng": lng,
        "display_name": display_name,
        "source": "photon",
    }
