from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.db.models import Driver, DriverStatusSnapshot
from app.domains.ride.route_service import haversine_km


DEMO_DRIVERS = [
    {"driver_id": "driver_demo_1", "name": "Nguyễn Minh", "vehicle": "VF e34", "lat": 10.7795, "lng": 106.6996, "battery_percent": 82, "status": "online"},
    {"driver_id": "driver_demo_2", "name": "Trần Hoàng", "vehicle": "VF 5", "lat": 10.7898, "lng": 106.7050, "battery_percent": 76, "status": "online"},
    {"driver_id": "driver_demo_3", "name": "Lê An", "vehicle": "Xanh Bike", "lat": 10.7711, "lng": 106.7042, "battery_percent": 91, "status": "online"},
]


def _db_driver_candidates(db: Session | None, *, limit: int = 30) -> list[dict]:
    if db is None:
        return []
    rows = (
        db.query(DriverStatusSnapshot, Driver)
        .join(Driver, Driver.id == DriverStatusSnapshot.driver_id)
        .filter(DriverStatusSnapshot.status.in_(["online", "available", "idle"]), Driver.status == "active")
        .order_by(DriverStatusSnapshot.created_at.desc())
        .limit(limit)
        .all()
    )
    candidates = []
    seen = set()
    for snapshot, driver in rows:
        if driver.id in seen or snapshot.lat is None or snapshot.lng is None:
            continue
        seen.add(driver.id)
        try:
            metadata = json.loads(snapshot.metadata_json or "{}")
        except json.JSONDecodeError:
            metadata = {}
        candidates.append(
            {
                "driver_id": driver.id,
                "name": driver.name,
                "vehicle": driver.vehicle_id or metadata.get("vehicle") or "VinFast",
                "lat": snapshot.lat,
                "lng": snapshot.lng,
                "battery_percent": snapshot.battery_percent,
                "status": snapshot.status,
            }
        )
    return candidates


def match_nearest_driver(pickup: dict | None, *, db: Session | None = None, service_type: str = "xanh_car") -> dict:
    if not pickup or pickup.get("lat") is None or pickup.get("lng") is None:
        return {"status": "missing_pickup", "driver": None, "candidates": []}
    candidates = _db_driver_candidates(db) or DEMO_DRIVERS
    ranked = []
    for driver in candidates:
        distance = haversine_km(float(pickup["lat"]), float(pickup["lng"]), float(driver["lat"]), float(driver["lng"]))
        ranked.append(
            {
                **driver,
                "distance_km": round(distance, 2),
                "eta_minutes": round(max(2.0, distance * 3.5 + 2), 1),
                "service_type": service_type,
            }
        )
    ranked.sort(key=lambda item: (item["eta_minutes"], item["distance_km"]))
    return {"status": "matched" if ranked else "no_driver", "driver": ranked[0] if ranked else None, "candidates": ranked[:5]}


def match_driver_stub() -> dict:
    return match_nearest_driver({"lat": 10.7769, "lng": 106.7009})["driver"]
