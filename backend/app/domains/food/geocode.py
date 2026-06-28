from __future__ import annotations

import requests

from app.config.settings import settings


def geocode_address(address: str | None) -> dict | None:
    if not address:
        return None
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1, "countrycodes": "vn"},
            headers={"User-Agent": settings.NOMINATIM_USER_AGENT},
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        first = data[0]
        return {"lat": float(first["lat"]), "lng": float(first["lon"]), "label": first.get("display_name")}
    except Exception:
        return None
