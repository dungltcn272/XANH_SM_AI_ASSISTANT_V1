from pydantic import BaseModel, Field


class TripStatusRequest(BaseModel):
    trip_id: str
    actor_id: str | None = None


class RideLocation(BaseModel):
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    label: str | None = None


class RideEstimateRequest(BaseModel):
    pickup: RideLocation
    dropoff: RideLocation
    service_type: str = Field(default="xanh_car", pattern="^(xanh_car|xanh_bike|premium)$")


class RideBookingRequest(RideEstimateRequest):
    confirm: bool = False
