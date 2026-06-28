from __future__ import annotations

import math

import requests

from app.config.settings import settings
from app.domains.ride.schemas import RideLocation


DEFAULT_POINTS = {
    "vinhomes central park": {"lat": 10.7949, "lng": 106.7219, "label": "Vinhomes Central Park"},
    "sân bay tân sơn nhất": {"lat": 10.8188, "lng": 106.6520, "label": "Sân bay Tân Sơn Nhất"},
    "san bay tan son nhat": {"lat": 10.8188, "lng": 106.6520, "label": "Sân bay Tân Sơn Nhất"},
    "tan son nhat": {"lat": 10.8188, "lng": 106.6520, "label": "Sân bay Tân Sơn Nhất"},
    "tsn": {"lat": 10.8188, "lng": 106.6520, "label": "Sân bay Tân Sơn Nhất"},
    "quận 1": {"lat": 10.7769, "lng": 106.7009, "label": "Quận 1, TP.HCM"},
    "quan 1": {"lat": 10.7769, "lng": 106.7009, "label": "Quận 1, TP.HCM"},
    "bến thành": {"lat": 10.7724, "lng": 106.6980, "label": "Chợ Bến Thành"},
    "ben thanh": {"lat": 10.7724, "lng": 106.6980, "label": "Chợ Bến Thành"},
}


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _known_point(address: str | None) -> dict | None:
    normalized = (address or "").casefold()
    for key, point in DEFAULT_POINTS.items():
        if key in normalized:
            return {**point, "address": address or point["label"], "provider": "known_point"}
    return None


def geocode_ride_location(location: RideLocation | dict | str) -> dict | None:
    if isinstance(location, str):
        payload = RideLocation(address=location)
    elif isinstance(location, dict):
        payload = RideLocation(**location)
    else:
        payload = location

    if payload.lat is not None and payload.lng is not None:
        return {
            "lat": float(payload.lat),
            "lng": float(payload.lng),
            "label": payload.label or payload.address or "Vị trí đã chọn",
            "address": payload.address or payload.label,
            "provider": "request",
        }

    known = _known_point(payload.address or payload.label)
    if known:
        return known

    address = payload.address or payload.label
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
        return {
            "lat": float(first["lat"]),
            "lng": float(first["lon"]),
            "label": payload.label or first.get("display_name") or address,
            "address": first.get("display_name") or address,
            "provider": "nominatim",
        }
    except Exception:
        return None


def _osrm_route(start: dict, end: dict) -> dict | None:
    try:
        coords = f"{start['lng']},{start['lat']};{end['lng']},{end['lat']}"
        response = requests.get(
            f"{settings.OSRM_BASE_URL.rstrip('/')}/route/v1/driving/{coords}",
            params={"overview": "full", "geometries": "geojson", "steps": "true"},
            headers={"User-Agent": settings.NOMINATIM_USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        routes = payload.get("routes") or []
        if not routes:
            return None
        route = routes[0]
        geometry = route.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        polyline = [[lat, lng] for lng, lat in coordinates if lat is not None and lng is not None]
        steps = []
        for leg in route.get("legs") or []:
            for step in leg.get("steps") or []:
                maneuver = step.get("maneuver") or {}
                steps.append(
                    {
                        "instruction": step.get("name") or maneuver.get("type") or "Tiếp tục",
                        "distance_m": round(float(step.get("distance") or 0), 1),
                        "duration_seconds": round(float(step.get("duration") or 0), 1),
                        "type": maneuver.get("type"),
                        "modifier": maneuver.get("modifier"),
                    }
                )
        return {
            "distance_km": round(float(route.get("distance") or 0) / 1000, 2),
            "eta_minutes": round(float(route.get("duration") or 0) / 60, 1),
            "polyline": polyline,
            "steps": steps[:25],
            "routing_provider": "osrm",
        }
    except Exception:
        return None


def build_route_preview(pickup: RideLocation | dict | str, dropoff: RideLocation | dict | str) -> dict:
    start = geocode_ride_location(pickup)
    end = geocode_ride_location(dropoff)
    if not start or not end:
        missing = []
        if not start:
            missing.append("pickup")
        if not end:
            missing.append("dropoff")
        return {"status": "missing_location", "missing": missing, "pickup": start, "dropoff": end}

    routed = _osrm_route(start, end)
    if routed:
        return {
            "status": "ok",
            "pickup": start,
            "dropoff": end,
            **routed,
        }

    straight = haversine_km(start["lat"], start["lng"], end["lat"], end["lng"])
    road_distance = max(0.8, straight * 1.28)
    eta = max(5.0, road_distance * 3.2 + 4)
    return {
        "status": "ok",
        "pickup": start,
        "dropoff": end,
        "distance_km": round(road_distance, 2),
        "eta_minutes": round(eta, 1),
        "polyline": [[start["lat"], start["lng"]], [end["lat"], end["lng"]]],
        "steps": [],
        "routing_provider": "haversine_internal",
    }


def route_preview() -> dict:
    return build_route_preview("Vinhomes Central Park", "Sân bay Tân Sơn Nhất")
