from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MapLayer = Literal["drivers", "restaurants", "demand", "traffic", "shortcuts", "start", "end"]
UserMode = Literal["customer", "driver"]


class GeoPoint(BaseModel):
    lat: float
    lng: float


class MapMarker(BaseModel):
    id: str
    type: Literal["driver", "restaurant", "demand", "traffic", "start", "end"]
    title: str
    description: str | None = None
    lat: float
    lng: float
    intensity: float = Field(default=0.5, ge=0, le=1)
    metadata: dict = Field(default_factory=dict)


class MapZone(BaseModel):
    id: str
    type: Literal["demand", "traffic", "driver_density"]
    title: str
    description: str | None = None
    center: GeoPoint
    radius_m: int
    intensity: float = Field(default=0.5, ge=0, le=1)
    metadata: dict = Field(default_factory=dict)


class MapRouteHint(BaseModel):
    id: str
    type: Literal["navigation", "traffic"] = "navigation"
    title: str
    description: str | None = None
    points: list[GeoPoint]
    eta_saving_minutes: int | None = None
    metadata: dict = Field(default_factory=dict)


class MapPayload(BaseModel):
    center: GeoPoint
    zoom: int = 14
    layers: list[MapLayer]
    markers: list[MapMarker] = Field(default_factory=list)
    zones: list[MapZone] = Field(default_factory=list)
    routes: list[MapRouteHint] = Field(default_factory=list)
    summary: str


class MapQuery(BaseModel):
    query: str
    lat: float | None = None
    lng: float | None = None
    radius_km: float = Field(default=4.0, ge=0.5, le=30)
    layers: list[MapLayer] | None = None
    user_mode: UserMode = "customer"
