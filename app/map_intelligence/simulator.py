import asyncio
import json
import random
import time
import math
import urllib.request
import traceback

from app.api.map_realtime import realtime_drivers_state

# Center: Hoan Kiem Lake, Hanoi
CENTER_LAT = 21.028511
CENTER_LNG = 105.854168
RADIUS_DEG = 0.05 # ~5km
NUM_DRIVERS = 30 # Giảm xuống 30 xe để chạy API OSRM mượt mà, tránh rate limit

def haversine(lon1, lat1, lon2, lat2):
    R = 6371000 # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_heading(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dlon)
    initial_bearing = math.atan2(y, x)
    return (math.degrees(initial_bearing) + 360) % 360

async def fetch_route(start_lat, start_lng, end_lat, end_lng):
    # Lấy đường đi từ OSRM API (GeoJSON)
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=full&geometries=geojson"
    loop = asyncio.get_event_loop()
    try:
        def fetch():
            req = urllib.request.Request(url, headers={'User-Agent': 'XanhSM-Simulator/1.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode())
        
        data = await loop.run_in_executor(None, fetch)
        if data and data.get("code") == "Ok":
            # coordinates: list of [lng, lat]
            return data["routes"][0]["geometry"]["coordinates"]
    except Exception as e:
        print(f"OSRM Error: {e}")
    return None

class Driver:
    def __init__(self, driver_id, lat=None, lng=None, vehicle_type=None):
        self.driver_id = driver_id
        self.lat = lat if lat is not None else CENTER_LAT + (random.random() - 0.5) * RADIUS_DEG
        self.lng = lng if lng is not None else CENTER_LNG + (random.random() - 0.5) * RADIUS_DEG
        self.dest_lat = None
        self.dest_lng = None
        self.status = "available" # available, busy, moving_to_pickup, in_trip
        self.speed = 0 # km/h
        self.heading = 0 # degree
        self.vehicle_type = vehicle_type if vehicle_type else ("bike" if random.random() < 0.7 else "car")
        
        self.rating = round(random.uniform(3.5, 5.0), 1)
        self.acceptance_rate = round(random.uniform(0.6, 1.0), 2)
        
        self.route_queue = []
        self.pickup_coord = None
        self.dropoff_coord = None
        self.current_booking_id = None

    async def pick_new_destination(self):
        if self.status != "available":
            return
            
        radius_km = 3.0
        r = radius_km / 111.0
        u = random.random()
        v = random.random()
        w = r * math.sqrt(u)
        t = 2 * math.pi * v
        x = w * math.cos(t)
        y = w * math.sin(t)
        
        self.dest_lat = CENTER_LAT + y
        self.dest_lng = CENTER_LNG + x
        
        # Async fetch route
        import urllib.request
        url = f"http://router.project-osrm.org/route/v1/driving/{self.lng},{self.lat};{self.dest_lng},{self.dest_lat}?overview=full&geometries=geojson"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, urllib.request.urlopen, req)
            data = json.loads(response.read().decode('utf-8'))
            if data["code"] == "Ok":
                coords = data["routes"][0]["geometry"]["coordinates"]
                self.route_queue = [(lat, lng) for lng, lat in coords]
        except Exception as e:
            self.route_queue = [(self.dest_lat, self.dest_lng)]

    def move(self):
        if not self.route_queue:
            return
            
        # Tốc độ lên 150-200 km/h để demo nhanh hơn
        self.speed = random.randint(150, 200)
        
        # Mô phỏng tắc nghẽn ở trung tâm Hoàn Kiếm (bán kính 1.5km)
        dist_to_center = haversine(self.lng, self.lat, 105.854168, 21.028511)
        if dist_to_center < 1500:
            self.speed = random.randint(10, 30) # Đi chậm (tắc đường)
        
        # Khoảng cách xe có thể đi được trong 1 tick (1 giây)
        distance_to_move = (self.speed * 1 / 3600) # km
        
        old_lat, old_lng = self.lat, self.lng
        
        while distance_to_move > 0 and self.route_queue:
            self.dest_lat, self.dest_lng = self.route_queue[0]
            dist = haversine(self.lng, self.lat, self.dest_lng, self.dest_lat) / 1000.0
            
            if dist <= distance_to_move:
                # Xe có đủ đà để chạy vượt qua waypoint này
                self.lat, self.lng = self.dest_lat, self.dest_lng
                distance_to_move -= dist
                self.route_queue.pop(0)
            else:
                # Xe chưa tới được waypoint, nhích lại gần
                move_ratio = distance_to_move / dist
                self.lat += (self.dest_lat - self.lat) * move_ratio
                self.lng += (self.dest_lng - self.lng) * move_ratio
                distance_to_move = 0
                
        if not self.route_queue:
            self.speed = 0
        
        if old_lat != self.lat or old_lng != self.lng:
            self.heading = calculate_heading(old_lat, old_lng, self.lat, self.lng)

    def get_data(self):
        return {
            "driver_id": self.driver_id,
            "lat": self.lat,
            "lng": self.lng,
            "heading": int(self.heading),
            "speed": self.speed,
            "vehicle_type": self.vehicle_type,
            "status": self.status,
            "rating": self.rating,
            "acceptance_rate": self.acceptance_rate,
            "timestamp": time.time()
        }

async def process_offer(send_queue, driver, booking_id, pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
    await asyncio.sleep(random.uniform(1.0, 3.0))
    driver_id = driver.driver_id
    
    # Kịch bản mô phỏng: 60% Accept, 20% Reject, 20% Ignore/Timeout
    rand = random.random()
    if rand < 0.6:
        # Accept
        payload = json.dumps({
            "type": "accept_offer",
            "booking_id": booking_id,
            "driver_id": driver_id
        })
        await send_queue.put(payload)
        print(f"Driver {driver_id} ACCEPTED booking {booking_id}")
        
        driver.current_booking_id = booking_id
        driver.pickup_coord = (pickup_lat, pickup_lng)
        driver.dropoff_coord = (dropoff_lat, dropoff_lng)
        
        # Đặt một flag để simulate_driver biết đang bận fetch
        driver.status = "fetching_route"
        
        # Fetch đường tới Pickup
        url = f"http://router.project-osrm.org/route/v1/driving/{driver.lng},{driver.lat};{pickup_lng},{pickup_lat}?overview=full&geometries=geojson"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, urllib.request.urlopen, req)
            data = json.loads(response.read().decode('utf-8'))
            if data["code"] == "Ok":
                coords = data["routes"][0]["geometry"]["coordinates"]
                driver.route_queue = [(lat, lng) for lng, lat in coords]
        except Exception as e:
            driver.route_queue = [driver.pickup_coord]
            
        # Set status AFTER route is populated
        driver.status = "moving_to_pickup"
            
    elif rand < 0.8:
        # Reject
        payload = json.dumps({
            "type": "reject_offer",
            "booking_id": booking_id,
            "driver_id": driver_id
        })
        await send_queue.put(payload)
        print(f"Driver {driver_id} REJECTED booking {booking_id}")
        driver.status = "available"
    else:
        # Ignore
        print(f"Driver {driver_id} IGNORED booking {booking_id} (Timeout)")

async def listen_messages(drivers, send_queue):
    # Dummy listener since we don't have websocket anymore
    driver_dict = {d.driver_id: d for d in drivers}
    while True:
        try:
            # We can still receive offers from an internal queue if needed, but for now just sleep
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Listen error: {e}")

async def simulate_driver(driver, send_queue):
    await asyncio.sleep(random.uniform(0.1, 5.0))
    await driver.pick_new_destination()

    while True:
        try:
            if driver.status == "available":
                if not driver.route_queue:
                    await driver.pick_new_destination()
                driver.move()
            elif driver.status == "moving_to_pickup":
                if not driver.route_queue:
                    # Đã tới điểm đón
                    driver.speed = 0
                    await asyncio.sleep(3) # Dừng 3s mô phỏng khách lên xe
                    
                    # Báo cho backend biết là đã đón khách
                    await send_queue.put(json.dumps({
                        "type": "driver_arrived",
                        "booking_id": driver.current_booking_id,
                        "driver_id": driver.driver_id
                    }))
                    
                    # Fetch đường tới Dropoff
                    url = f"http://router.project-osrm.org/route/v1/driving/{driver.lng},{driver.lat};{driver.dropoff_coord[1]},{driver.dropoff_coord[0]}?overview=full&geometries=geojson"
                    try:
                        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                        loop = asyncio.get_event_loop()
                        response = await loop.run_in_executor(None, urllib.request.urlopen, req)
                        data = json.loads(response.read().decode('utf-8'))
                        if data["code"] == "Ok":
                            coords = data["routes"][0]["geometry"]["coordinates"]
                            driver.route_queue = [(lat, lng) for lng, lat in coords]
                    except Exception as e:
                        driver.route_queue = [driver.dropoff_coord]
                    
                    driver.status = "in_trip"
                else:
                    driver.move()
            elif driver.status == "in_trip":
                if not driver.route_queue:
                    # Đã tới đích
                    driver.speed = 0
                    await asyncio.sleep(3)
                    driver.status = "available"
                    # Báo hoàn thành cuốc
                    await send_queue.put(json.dumps({
                        "type": "trip_completed",
                        "booking_id": driver.current_booking_id,
                        "driver_id": driver.driver_id
                    }))
                    driver.current_booking_id = None
                    await driver.pick_new_destination()
                else:
                    driver.move()
                
            payload = json.dumps(driver.get_data())
            await send_queue.put(payload)
            await asyncio.sleep(1) # Cập nhật mỗi 1 giây thay vì 2 giây
        except Exception as e:
            print(f"Error for {driver.driver_id}: {e}")
            await asyncio.sleep(1)

async def ws_sender(send_queue):
    try:
        while True:
            payload_str = await send_queue.get()
            payload = json.loads(payload_str)
            if "driver_id" in payload and "lat" in payload:
                driver_id = payload["driver_id"]
                realtime_drivers_state[driver_id] = payload
    except Exception as e:
        print(f"Sender error: {e}")

async def user_generator_loop():
    import urllib.request
    await asyncio.sleep(10) # Đợi backend khởi động xong
    print("Started User Generator Loop...")
    while True:
        try:
            # Tạo 1 user ảo ở khu vực Bờ Hồ hoặc Cầu Giấy
            center_lat = 21.028511
            center_lng = 105.854168
            
            p_lat = center_lat + random.uniform(-0.02, 0.02)
            p_lng = center_lng + random.uniform(-0.02, 0.02)
            
            d_lat = center_lat + random.uniform(-0.05, 0.05)
            d_lng = center_lng + random.uniform(-0.05, 0.05)
            
            payload = json.dumps({
                "pickup_lat": p_lat,
                "pickup_lng": p_lng,
                "dropoff_lat": d_lat,
                "dropoff_lng": d_lng
            }).encode('utf-8')
            
            req = urllib.request.Request("http://localhost:8000/api/bookings/book", data=payload, headers={'Content-Type': 'application/json'})
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, urllib.request.urlopen, req)
            data = json.loads(response.read().decode('utf-8'))
            print(f"Mock User created booking: {data.get('booking_id')}")
            
        except Exception as e:
            print(f"Failed to create mock user: {e}")
            
        await asyncio.sleep(random.uniform(5.0, 15.0)) # 5 đến 15 giây tạo 1 khách

async def start_simulator():
    print("Starting simulator inside Backend Service...")
    try:
        send_queue = asyncio.Queue()
        
        drivers = [Driver(f"D{str(i+1).zfill(3)}") for i in range(NUM_DRIVERS)]
        
        tasks = [asyncio.create_task(simulate_driver(driver, send_queue)) for driver in drivers]
        tasks.append(asyncio.create_task(listen_messages(drivers, send_queue)))
        tasks.append(asyncio.create_task(ws_sender(send_queue)))
        tasks.append(asyncio.create_task(user_generator_loop()))
        
        await asyncio.gather(*tasks)
    except Exception as e:
        print(f"Simulator failed: {e}")
