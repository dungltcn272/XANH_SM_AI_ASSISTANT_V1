from __future__ import annotations

import re
import unicodedata

from sqlalchemy.orm import Session

from app.db.models import Trip
from app.domains.ride.driver_matching import match_nearest_driver
from app.domains.ride.fare_service import estimate_fare
from app.domains.ride.route_service import build_route_preview
from app.domains.ride.schemas import RideBookingRequest, RideEstimateRequest, RideLocation


def _location_label(location: dict | None) -> str:
    if not location:
        return "chưa rõ"
    return location.get("label") or location.get("address") or "vị trí đã chọn"


def _answer_for_preview(route: dict, fare: dict | None, driver_match: dict | None, *, confirmed: bool = False) -> str:
    if route.get("status") != "ok":
        missing = ", ".join(route.get("missing") or [])
        return f"Mình cần thêm thông tin {missing or 'điểm đón/điểm đến'} để đặt xe cho bạn."

    driver = (driver_match or {}).get("driver")
    fare_text = f"{fare['estimated_fare_vnd']:,}đ".replace(",", ".") if fare else "đang tính"
    if confirmed:
        return (
            f"Mình đã tạo yêu cầu đặt xe từ {_location_label(route.get('pickup'))} đến {_location_label(route.get('dropoff'))}. "
            f"Quãng đường khoảng {route['distance_km']} km, ETA chuyến {route['eta_minutes']} phút, giá tạm tính {fare_text}. "
            f"Tài xế phù hợp nhất: {driver['name']} cách {driver['distance_km']} km, đến điểm đón khoảng {driver['eta_minutes']} phút."
            if driver
            else f"Mình đã tạo yêu cầu đặt xe, giá tạm tính {fare_text}. Hiện chưa có tài xế phù hợp ngay gần điểm đón."
        )
    return (
        f"Ước tính chuyến đi từ {_location_label(route.get('pickup'))} đến {_location_label(route.get('dropoff'))}: "
        f"{route['distance_km']} km, khoảng {route['eta_minutes']} phút, giá tạm tính {fare_text}. "
        f"Tài xế gần nhất có thể đến trong {driver['eta_minutes']} phút."
        if driver
        else f"Ước tính chuyến đi: {route['distance_km']} km, khoảng {route['eta_minutes']} phút, giá tạm tính {fare_text}."
    )


def estimate_ride(req: RideEstimateRequest, *, db: Session | None = None) -> dict:
    route = build_route_preview(req.pickup, req.dropoff)
    fare = None
    driver_match = None
    if route.get("status") == "ok":
        fare = estimate_fare(route["distance_km"], service_type=req.service_type, duration_minutes=route["eta_minutes"])
        driver_match = match_nearest_driver(route.get("pickup"), db=db, service_type=req.service_type)
    return {
        "answer": _answer_for_preview(route, fare, driver_match),
        "status": route.get("status"),
        "service_type": req.service_type,
        "route": route,
        "fare": fare,
        "driver_match": driver_match,
    }


def create_booking(req: RideBookingRequest, *, db: Session | None = None, actor_id: str | None = None) -> dict:
    preview = estimate_ride(req, db=db)
    if preview["status"] != "ok":
        return preview

    trip_id = None
    driver = (preview.get("driver_match") or {}).get("driver") or {}
    if db is not None:
        route = preview["route"]
        fare = preview["fare"] or {}
        trip = Trip(
            customer_actor_id=actor_id,
            driver_id=driver.get("driver_id") if not str(driver.get("driver_id", "")).startswith("driver_demo") else None,
            status="requested" if req.confirm else "preview",
            pickup_address=route["pickup"].get("address") or route["pickup"].get("label"),
            pickup_lat=route["pickup"].get("lat"),
            pickup_lng=route["pickup"].get("lng"),
            dropoff_address=route["dropoff"].get("address") or route["dropoff"].get("label"),
            dropoff_lat=route["dropoff"].get("lat"),
            dropoff_lng=route["dropoff"].get("lng"),
            estimated_fare=fare.get("estimated_fare_vnd"),
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)
        trip_id = trip.id

    preview["trip_id"] = trip_id
    preview["status"] = "requested" if req.confirm else "preview"
    preview["answer"] = _answer_for_preview(preview["route"], preview["fare"], preview["driver_match"], confirmed=req.confirm)
    return preview


def create_booking_stub(pickup: str, dropoff: str) -> dict:
    req = RideBookingRequest(pickup=RideLocation(address=pickup), dropoff=RideLocation(address=dropoff), confirm=False)
    return create_booking(req)


def parse_ride_request_from_query(query: str) -> RideBookingRequest | None:
    normalized = " ".join(query.strip().split())
    patterns = [
        r"(?:đặt xe|gọi xe|book xe).*?từ\s+(?P<pickup>.+?)\s+(?:đến|tới|về)\s+(?P<dropoff>.+)",
        r"từ\s+(?P<pickup>.+?)\s+(?:đến|tới|về)\s+(?P<dropoff>.+)",
        r"(?:dat xe|goi xe|book xe).*?tu\s+(?P<pickup>.+?)\s+(?:den|toi|ve)\s+(?P<dropoff>.+)",
        r"tu\s+(?P<pickup>.+?)\s+(?:den|toi|ve)\s+(?P<dropoff>.+)",
    ]
    folded = unicodedata.normalize("NFD", normalized.casefold())
    folded = "".join(char for char in folded if unicodedata.category(char) != "Mn")
    for pattern in patterns[:2]:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            continue
        pickup = match.group("pickup").strip(" ,.;")
        dropoff = match.group("dropoff").strip(" ,.;")
        if pickup and dropoff:
            service_type = "xanh_bike" if any(term in normalized.casefold() for term in ("bike", "xe máy", "xanh bike")) else "xanh_car"
            confirm = any(term in normalized.casefold() for term in ("đặt luôn", "xác nhận", "confirm", "gọi luôn"))
            return RideBookingRequest(
                pickup=RideLocation(address=pickup),
                dropoff=RideLocation(address=dropoff),
                service_type=service_type,
                confirm=confirm,
            )
    for pattern in patterns[2:]:
        match = re.search(pattern, folded, flags=re.IGNORECASE)
        if not match:
            continue
        pickup = match.group("pickup").strip(" ,.;")
        dropoff = match.group("dropoff").strip(" ,.;")
        if pickup and dropoff:
            service_type = "xanh_bike" if any(term in folded for term in ("bike", "xe may", "xanh bike")) else "xanh_car"
            confirm = any(term in folded for term in ("dat luon", "xac nhan", "confirm", "goi luon"))
            return RideBookingRequest(
                pickup=RideLocation(address=pickup),
                dropoff=RideLocation(address=dropoff),
                service_type=service_type,
                confirm=confirm,
            )
    return None


def ride_support_from_query(query: str, *, db: Session | None = None, actor_id: str | None = None) -> dict:
    req = parse_ride_request_from_query(query)
    if req is None:
        return {
            "answer": "Bạn cho mình điểm đón và điểm đến theo mẫu: `đặt xe từ [điểm đón] đến [điểm đến]` nhé.",
            "status": "missing_location",
        }
    return create_booking(req, db=db, actor_id=actor_id)
