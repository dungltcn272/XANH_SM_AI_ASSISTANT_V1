from __future__ import annotations

import math
from typing import Iterable

from app.map_intelligence.fake_data import (
    DEFAULT_HCM_CENTER,
    DEMAND_MARKERS,
    DRIVER_MARKERS,
    RESTAURANT_MARKERS,
    ROUTES,
    TRAFFIC_MARKERS,
    ZONES,
)
from app.map_intelligence.schemas import GeoPoint, MapLayer, MapPayload, MapQuery, MapRouteHint, MapZone


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class MapIntelligenceService:
    def infer_layers(self, query: str, layers: list[MapLayer] | None = None) -> list[MapLayer]:
        if layers:
            return layers
        text = (query or "").lower()
        selected: list[MapLayer] = []
        if any(term in text for term in ["tài xế", "tai xe", "driver", "xe quanh", "đông xe"]):
            selected.append("drivers")
        if any(term in text for term in ["quán", "quan", "ăn", "an", "food", "nhà hàng", "restaurant"]):
            selected.append("restaurants")
        if any(term in text for term in ["đông khách", "dong khach", "nhu cầu", "nhu cau", "hotspot", "điểm đông"]):
            selected.append("demand")
        if any(term in text for term in ["tắc", "tac", "kẹt", "ket", "traffic", "ùn", "un"]):
            selected.append("traffic")
        if any(term in text for term in ["đường tắt", "duong tat", "né", "ne", "shortcut", "đường nhanh"]):
            selected.append("shortcuts")
        return selected or ["drivers", "restaurants", "demand"]

    def get_payload(self, req: MapQuery) -> MapPayload:
        center = GeoPoint(lat=req.lat or DEFAULT_HCM_CENTER.lat, lng=req.lng or DEFAULT_HCM_CENTER.lng)
        layers = self.infer_layers(req.query, req.layers)
        markers = []
        zones: list[MapZone] = []
        routes: list[MapRouteHint] = []

        if "drivers" in layers:
            markers.extend(DRIVER_MARKERS)
            zones.extend(zone for zone in ZONES if zone.type == "driver_density")
        if "restaurants" in layers:
            markers.extend(RESTAURANT_MARKERS)
        if "demand" in layers:
            markers.extend(DEMAND_MARKERS)
            zones.extend(zone for zone in ZONES if zone.type == "demand")
        if "traffic" in layers:
            markers.extend(TRAFFIC_MARKERS)
            zones.extend(zone for zone in ZONES if zone.type == "traffic")
        if "shortcuts" in layers:
            routes.extend(ROUTES)

        radius_km = req.radius_km or 4.0
        markers = [
            marker.model_copy(update={"metadata": {**marker.metadata, "distance_km": round(haversine_km(center.lat, center.lng, marker.lat, marker.lng), 2)}})
            for marker in markers
            if haversine_km(center.lat, center.lng, marker.lat, marker.lng) <= radius_km
        ]
        zones = [
            zone
            for zone in zones
            if haversine_km(center.lat, center.lng, zone.center.lat, zone.center.lng) <= radius_km + (zone.radius_m / 1000)
        ]
        routes = [
            route
            for route in routes
            if self._route_near_center(route.points, center, radius_km)
        ]

        return MapPayload(
            center=center,
            zoom=14 if radius_km <= 5 else 12,
            layers=layers,
            markers=markers,
            zones=zones,
            routes=routes,
            summary=self.summarize(req, markers, zones, routes),
        )

    def summarize(self, req: MapQuery, markers: Iterable, zones: Iterable[MapZone], routes: Iterable[MapRouteHint]) -> str:
        markers = list(markers)
        zones = list(zones)
        routes = list(routes)
        driver_count = sum(int(marker.metadata.get("drivers", 1)) for marker in markers if marker.type == "driver")
        restaurant_count = sum(1 for marker in markers if marker.type == "restaurant")
        demand_count = sum(1 for marker in markers if marker.type == "demand") + sum(1 for zone in zones if zone.type == "demand")
        traffic_count = sum(1 for marker in markers if marker.type == "traffic") + sum(1 for zone in zones if zone.type == "traffic")

        if req.user_mode == "driver":
            best_zone = max((zone for zone in zones if zone.type == "demand"), key=lambda item: item.intensity, default=None)
            if best_zone:
                return f"Khu {best_zone.title} đang có tín hiệu đông khách nhất trong dữ liệu demo; tài xế nên đứng gần rìa vùng để dễ nhận cuốc và tránh điểm tắc."
            return "Dữ liệu demo chưa thấy điểm cầu nổi bật quanh vị trí này; nên ưu tiên khu trung tâm hoặc điểm gần nhà hàng/văn phòng."

        parts = []
        if driver_count:
            parts.append(f"khoảng {driver_count} tài xế")
        if restaurant_count:
            parts.append(f"{restaurant_count} quán ăn")
        if demand_count:
            parts.append(f"{demand_count} điểm/vùng đông khách")
        if traffic_count:
            parts.append(f"{traffic_count} điểm/vùng tắc")
        if routes:
            parts.append(f"{len(routes)} gợi ý đường tắt")
        if not parts:
            return "Dữ liệu demo chưa có tín hiệu nổi bật quanh vị trí này."
        return "Em tìm thấy " + ", ".join(parts) + " quanh khu vực anh/chị đang xem."

    def _route_near_center(self, points: list[GeoPoint], center: GeoPoint, radius_km: float) -> bool:
        return any(haversine_km(center.lat, center.lng, point.lat, point.lng) <= radius_km for point in points)
