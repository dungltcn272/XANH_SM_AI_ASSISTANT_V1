from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependency import get_current_entity, get_db
from app.domains.ride.booking_service import create_booking, create_booking_stub, estimate_ride
from app.domains.ride.fare_service import estimate_fare
from app.domains.ride.schemas import RideBookingRequest, RideEstimateRequest, RideLocation


router = APIRouter()


class BookingRequest(BaseModel):
    pickup: str | RideLocation
    dropoff: str | RideLocation
    service_type: str = "xanh_car"
    confirm: bool = False


def _actor_id(current_entity: dict) -> str | None:
    entity = current_entity.get("entity")
    return getattr(entity, "id", None)


def _location(value: str | RideLocation) -> RideLocation:
    if isinstance(value, RideLocation):
        return value
    return RideLocation(address=value)


@router.post("")
def create_booking_endpoint(
    req: BookingRequest,
    db: Session = Depends(get_db),
    current_entity: dict = Depends(get_current_entity),
) -> dict:
    ride_req = RideBookingRequest(
        pickup=_location(req.pickup),
        dropoff=_location(req.dropoff),
        service_type=req.service_type,
        confirm=req.confirm,
    )
    return create_booking(ride_req, db=db, actor_id=_actor_id(current_entity))


@router.post("/estimate")
def estimate_ride_endpoint(req: RideEstimateRequest, db: Session = Depends(get_db)) -> dict:
    return estimate_ride(req, db=db)


@router.get("/preview")
def preview(pickup: str = "Vinhomes Central Park", dropoff: str = "Sân bay Tân Sơn Nhất", service_type: str = "xanh_car", db: Session = Depends(get_db)) -> dict:
    return estimate_ride(
        RideEstimateRequest(pickup=RideLocation(address=pickup), dropoff=RideLocation(address=dropoff), service_type=service_type),
        db=db,
    )


@router.get("/fare-estimate")
def fare(distance_km: float, service_type: str = "xanh_car", duration_minutes: float | None = None) -> dict:
    return estimate_fare(distance_km, service_type=service_type, duration_minutes=duration_minutes)
