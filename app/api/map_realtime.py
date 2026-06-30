from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for driver states
realtime_drivers_state: Dict[str, Any] = {}

class BookingRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float

@router.websocket("/ws/simulator")
async def simulator_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for the simulator script to push driver states.
    """
    await websocket.accept()
    logger.info("Simulator connected to WebSocket")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                # payload could be a driver update, accept_offer, trip_completed, etc.
                if "driver_id" in payload and "lat" in payload and "lng" in payload:
                    driver_id = payload["driver_id"]
                    realtime_drivers_state[driver_id] = payload
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        logger.info("Simulator disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

@router.post("/api/bookings/book")
async def mock_booking(request: BookingRequest):
    """
    Mock endpoint for simulator to create dummy bookings.
    """
    import uuid
    booking_id = f"bkg_{uuid.uuid4().hex[:8]}"
    return {"status": "success", "booking_id": booking_id}

@router.get("/api/map/realtime-vehicles")
async def get_realtime_vehicles(lat: float, lng: float, radius_km: float = 15.0, lat2: float = None, lng2: float = None):
    """
    Endpoint for Frontend to fetch real-time vehicles nearby.
    """
    import math

    def calc_dist(lat1, lng1, lat2, lng2):
        R = 6371  # Radius of the earth in km
        dLat = math.radians(lat2 - lat1)
        dLng = math.radians(lng2 - lng1)
        a = math.sin(dLat/2) * math.sin(dLat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dLng/2) * math.sin(dLng/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    # Lọc xe trong bán kính
    drivers = []
    for d in realtime_drivers_state.values():
        dist1 = calc_dist(lat, lng, d["lat"], d["lng"])
        dist2 = calc_dist(lat2, lng2, d["lat"], d["lng"]) if lat2 is not None and lng2 is not None else float('inf')
        
        min_dist = min(dist1, dist2)
        if min_dist <= radius_km:
            d_copy = dict(d)
            d_copy["distance"] = min_dist
            drivers.append(d_copy)
            
    # Sort by distance and get top 200
    drivers.sort(key=lambda x: x["distance"])
    drivers = drivers[:200]
    
    return {"success": True, "drivers": drivers}
