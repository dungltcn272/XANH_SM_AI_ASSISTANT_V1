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
async def get_realtime_vehicles(lat: float, lng: float, radius_km: float = 5.0):
    """
    Endpoint for Frontend to fetch real-time vehicles nearby.
    """
    # Simply return all active drivers for now
    drivers = list(realtime_drivers_state.values())
    return {"success": True, "drivers": drivers}
