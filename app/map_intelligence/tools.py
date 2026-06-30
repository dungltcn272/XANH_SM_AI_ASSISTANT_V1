import json
import logging
import requests
from typing import Any
from urllib.parse import quote

logger = logging.getLogger(__name__)

def search_places(query: str, lat: float, lng: float, radius_km: float = 5.0) -> dict[str, Any]:
    """
    Tìm kiếm toạ độ của một địa danh (ví dụ "Nhà thờ Đức Bà", "Landmark 81") xung quanh vị trí hiện tại.
    Sử dụng OpenStreetMap Nominatim API.
    """
    logger.info(f"[MAP_TOOL] search_places: query={query}, lat={lat}, lng={lng}")
    try:
        # Nominatim search
        url = f"https://nominatim.openstreetmap.org/search?q={quote(query)}&format=json&limit=1"
        # Bổ sung viewbox để ưu tiên kết quả gần vị trí hiện tại
        if lat and lng:
            delta = radius_km / 111.0 # 1 độ ~ 111km
            viewbox = f"{lng-delta},{lat+delta},{lng+delta},{lat-delta}"
            url += f"&viewbox={viewbox}&bounded=0"

        headers = {
            "User-Agent": "GreenSM-AI-Assistant/1.0"
        }
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 0:
                result = data[0]
                return {
                    "found": True,
                    "title": result.get("display_name", query),
                    "lat": float(result["lat"]),
                    "lng": float(result["lon"]),
                }
    except Exception as e:
        logger.error(f"[MAP_TOOL] search_places error: {e}")
    
    return {"found": False, "message": "Không tìm thấy kết quả phù hợp."}


def get_osrm_routes(start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> dict[str, Any]:
    """
    Lấy thông định tuyến và khoảng cách từ OSRM. Trả về thông tin tuyến đường.
    """
    logger.info(f"[MAP_TOOL] get_osrm_routes: {start_lat},{start_lng} -> {end_lat},{end_lng}")
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=full&geometries=geojson&alternatives=true"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            routes = data.get("routes", [])
            results = []
            for i, route in enumerate(routes):
                distance_km = route.get("distance", 0) / 1000.0
                duration_min = route.get("duration", 0) / 60.0
                coords = route.get("geometry", {}).get("coordinates", [])
                # OSRM trả về [lon, lat], ta đổi thành [lat, lon] cho Frontend
                points = [{"lat": lat, "lng": lon} for lon, lat in coords]
                
                results.append({
                    "id": f"route_{i}",
                    "title": "Tuyến chính" if i == 0 else f"Tuyến thay thế {i}",
                    "distance_km": round(distance_km, 1),
                    "duration_min": round(duration_min, 1),
                    "points": points
                })
            
            return {"success": True, "routes": results}
    except Exception as e:
        logger.error(f"[MAP_TOOL] get_osrm_routes error: {e}")
    
    return {"success": False, "message": "Lỗi khi gọi OSRM API."}


def get_traffic_zones(lat: float, lng: float, radius_km: float = 5.0) -> dict[str, Any]:
    """
    Giả lập API trả về các vùng kẹt xe gần vị trí người dùng.
    """
    logger.info(f"[MAP_TOOL] get_traffic_zones: lat={lat}, lng={lng}")
    from app.map_intelligence.fake_data import ZONES
    
    # Lấy các vùng kẹt xe từ fake data
    traffic_zones = [z for z in ZONES if z.type == "traffic"]
    
    # Lọc những vùng nằm trong bán kính radius_km
    filtered_zones = []
    for z in traffic_zones:
        dist = ((z.center.lat - lat)**2 + (z.center.lng - lng)**2)**0.5 * 111.0
        if dist <= radius_km:
            filtered_zones.append(z)
            
    # Giả lập trả về các vùng kẹt xe dưới dạng đường (lines)
    results = []
    for z in filtered_zones:
        points = [
            {"lat": z.center.lat - 0.002, "lng": z.center.lng - 0.002},
            {"lat": z.center.lat, "lng": z.center.lng},
            {"lat": z.center.lat + 0.002, "lng": z.center.lng + 0.002}
        ]
        results.append({
            "id": z.id,
            "type": "traffic",
            "title": z.title,
            "description": z.description,
            "points": points,
            "metadata": {"delay_minutes": z.intensity * 20},
        })
    return {"success": True, "lines": results}


def get_driver_density(lat: float, lng: float, radius_km: float = 5.0) -> dict[str, Any]:
    """
    Giả lập API trả về phân bổ tài xế gần vị trí người dùng.
    """
    logger.info(f"[MAP_TOOL] get_driver_density: lat={lat}, lng={lng}")
    from app.map_intelligence.fake_data import DRIVER_MARKERS, ZONES
    
    drvs = [m for m in DRIVER_MARKERS if m.type == "driver"]
    zones = [z for z in ZONES if z.type == "driver_density"]
    
    markers_res = []
    for m in drvs:
        dist = ((m.lat - lat)**2 + (m.lng - lng)**2)**0.5 * 111.0
        if dist <= radius_km:
            markers_res.append({
                "id": m.id,
                "type": m.type,
                "title": m.title,
                "description": m.description,
                "lat": m.lat,
                "lng": m.lng,
                "intensity": m.intensity,
            })
        
    zones_res = []
    for z in zones:
        dist = ((z.center.lat - lat)**2 + (z.center.lng - lng)**2)**0.5 * 111.0
        if dist <= radius_km:
            zones_res.append({
                "id": z.id,
                "type": z.type,
                "title": z.title,
                "description": z.description,
                "center": {"lat": z.center.lat, "lng": z.center.lng},
                "radius_m": z.radius_m,
            })
        
    return {"success": True, "markers": markers_res, "zones": zones_res}
