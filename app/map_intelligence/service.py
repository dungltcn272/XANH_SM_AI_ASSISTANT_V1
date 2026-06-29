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


def get_osrm_route(lat1: float, lng1: float, lat2: float, lng2: float) -> dict | None:
    """Gọi OSRM API để lấy thông tin định tuyến (đường đi, khoảng cách, thời gian)"""
    import requests
    url = f"http://router.project-osrm.org/route/v1/driving/{lng1},{lat1};{lng2},{lat2}?overview=full&geometries=geojson"
    try:
        resp = requests.get(url, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == "Ok" and len(data.get("routes", [])) > 0:
                route = data["routes"][0]
                distance_km = route.get("distance", 0) / 1000.0
                duration_min = route.get("duration", 0) / 60.0
                coords = route.get("geometry", {}).get("coordinates", [])
                points = [GeoPoint(lat=lat, lng=lng) for lng, lat in coords]
                return {
                    "distance_km": distance_km,
                    "duration_min": duration_min,
                    "points": points
                }
    except Exception:
        pass
    return None

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

        # Luôn trả về toàn bộ dữ liệu để Frontend có thể tự do bật/tắt (toggle) các lớp
        markers.extend(DRIVER_MARKERS)
        zones.extend(zone for zone in ZONES if zone.type == "driver_density")
        markers.extend(RESTAURANT_MARKERS)
        markers.extend(DEMAND_MARKERS)
        markers.extend(TRAFFIC_MARKERS)
        zones.extend(zone for zone in ZONES if zone.type in ["traffic", "demand"])
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

        # Calculate real OSRM route to the nearest relevant point
        nearest = None
        if "restaurants" in layers:
            rests = [m for m in markers if m.type == "restaurant"]
            if rests:
                nearest = min(rests, key=lambda m: m.metadata.get("distance_km", 999))
        elif "drivers" in layers:
            drvs = [m for m in markers if m.type == "driver"]
            if drvs:
                nearest = min(drvs, key=lambda m: m.metadata.get("distance_km", 999))
        
        if nearest:
            osrm = get_osrm_route(center.lat, center.lng, nearest.lat, nearest.lng)
            if osrm:
                routes.append(
                    MapRouteHint(
                        points=osrm["points"],
                        title=f"Tuyến đường tới {nearest.title}",
                        description=f"Quãng đường: {osrm['distance_km']:.1f} km - Thời gian lái xe: {osrm['duration_min']:.0f} phút"
                    )
                )

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
            best_zone = max((zone for zone in zones if zone.type in ["demand", "driver_density"]), key=lambda item: item.intensity, default=None)
            if best_zone:
                if best_zone.type == "driver_density":
                    return f"Khu {best_zone.title} đang có lượng tài xế hoạt động dày đặc nhất; khách hàng sẽ dễ gọi xe nhanh."
                if best_zone.type == "demand":
                    return f"Khu {best_zone.title} đang có tín hiệu đông khách nhất trong dữ liệu hệ thống; tài xế nên đứng gần rìa vùng để dễ nhận cuốc và tránh điểm tắc."
                return f"Vùng nổi bật nhất hiện tại là {best_zone.title}."
            return "Dữ liệu hệ thống chưa thấy điểm cầu nổi bật quanh vị trí này; nên ưu tiên khu trung tâm hoặc điểm gần nhà hàng/văn phòng."

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
            summary_text = "Hệ thống chưa có thông tin nổi bật quanh vị trí này."
        else:
            summary_text = "Có " + ", ".join(parts) + " quanh khu vực anh/chị đang xem."
            
        real_routes = [r for r in routes if "Thời gian lái xe" in r.description]
        if real_routes:
            summary_text += f"\nThông tin định tuyến thực tế: Tuyến đường tới điểm gần nhất dài {real_routes[0].description}."
            
        return summary_text

    def _route_near_center(self, points: list[GeoPoint], center: GeoPoint, radius_km: float) -> bool:
        return any(haversine_km(center.lat, center.lng, point.lat, point.lng) <= radius_km for point in points)
