from __future__ import annotations


FARE_TABLE = {
    "xanh_bike": {"base": 10000, "per_km": 6200, "minimum": 18000},
    "xanh_car": {"base": 12000, "per_km": 14500, "minimum": 35000},
    "premium": {"base": 18000, "per_km": 19000, "minimum": 55000},
}


def estimate_fare(distance_km: float, *, service_type: str = "xanh_car", duration_minutes: float | None = None) -> dict:
    pricing = FARE_TABLE.get(service_type, FARE_TABLE["xanh_car"])
    duration = duration_minutes or max(5.0, distance_km * 3.2 + 4)
    raw = int(pricing["base"] + distance_km * pricing["per_km"] + duration * 900)
    estimated = max(pricing["minimum"], int(round(raw / 1000) * 1000))
    return {
        "service_type": service_type,
        "distance_km": round(distance_km, 2),
        "duration_minutes": round(duration, 1),
        "estimated_fare_vnd": estimated,
        "currency": "VND",
        "pricing": pricing,
    }
