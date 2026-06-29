from __future__ import annotations

from fastapi import APIRouter, Query

from app.map_intelligence.schemas import MapLayer, MapQuery
from app.map_intelligence.service import MapIntelligenceService

router = APIRouter()
service = MapIntelligenceService()


@router.get("/layers")
def get_map_layers(
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float = Query(default=5.0, ge=0.5, le=30),
    layers: str | None = None,
):
    parsed_layers = _parse_layers(layers)
    payload = service.get_payload(
        MapQuery(
            query="map layers",
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            layers=parsed_layers,
        )
    )
    return payload.model_dump()


@router.post("/query")
def query_map(req: MapQuery):
    return service.get_payload(req).model_dump()


def _parse_layers(value: str | None) -> list[MapLayer] | None:
    if not value:
        return None
    valid = {"drivers", "restaurants", "demand", "traffic", "shortcuts"}
    parsed = [item.strip() for item in value.split(",") if item.strip() in valid]
    return parsed or None
