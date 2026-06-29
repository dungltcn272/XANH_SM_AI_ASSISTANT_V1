from __future__ import annotations

from app.map_intelligence.schemas import GeoPoint, MapMarker, MapRouteHint, MapZone

DEFAULT_HCM_CENTER = GeoPoint(lat=10.7769, lng=106.7009)
DEFAULT_HN_CENTER = GeoPoint(lat=21.0278, lng=105.8342)

DRIVER_MARKERS = [
    MapMarker(id="drv_hcm_001", type="driver", title="Cụm tài xế Bến Thành", description="Khoảng 18 tài xế online trong bán kính gần 600m.", lat=10.7721, lng=106.6983, intensity=0.82, metadata={"drivers": 18, "vehicle_mix": "car,bike"}),
    MapMarker(id="drv_hcm_002", type="driver", title="Cụm tài xế Nguyễn Huệ", description="Nguồn cung tốt, phù hợp đón khách văn phòng và du lịch.", lat=10.7747, lng=106.7036, intensity=0.74, metadata={"drivers": 14, "vehicle_mix": "car"}),
    MapMarker(id="drv_hcm_003", type="driver", title="Cụm tài xế Thảo Điền", description="Tài xế phân bố thưa hơn nhưng nhu cầu di chuyển cao buổi tối.", lat=10.8027, lng=106.7338, intensity=0.64, metadata={"drivers": 9, "vehicle_mix": "car,bike"}),
    MapMarker(id="drv_hn_001", type="driver", title="Cụm tài xế Hồ Gươm", description="Nguồn cung dày quanh phố đi bộ và khách sạn.", lat=21.0287, lng=105.8521, intensity=0.86, metadata={"drivers": 20, "vehicle_mix": "car,bike"}),
    MapMarker(id="drv_hn_002", type="driver", title="Cụm tài xế Cầu Giấy", description="Nguồn cung ổn định quanh văn phòng và trường đại học.", lat=21.0368, lng=105.7909, intensity=0.72, metadata={"drivers": 15, "vehicle_mix": "bike"}),
]

RESTAURANT_MARKERS = [
    MapMarker(id="res_hcm_001", type="restaurant", title="Phở Xanh Pasteur", description="Phở bò, mở cửa đến 22:00, rating 4.7.", lat=10.7777, lng=106.6976, intensity=0.78, metadata={"category": "pho", "rating": 4.7, "eta_minutes": 16}),
    MapMarker(id="res_hcm_002", type="restaurant", title="Cơm Tấm Trưa Nhanh", description="Phù hợp bữa trưa văn phòng, giá 45.000đ.", lat=10.7812, lng=106.7041, intensity=0.7, metadata={"category": "com tam", "rating": 4.5, "eta_minutes": 14}),
    MapMarker(id="res_hcm_003", type="restaurant", title="Bún Bò Sài Gòn", description="Đông đơn vào tối, bán kính giao 5km.", lat=10.7688, lng=106.6928, intensity=0.66, metadata={"category": "bun bo", "rating": 4.4, "eta_minutes": 20}),
    MapMarker(id="res_hn_001", type="restaurant", title="Bún Chả Phố Cổ", description="Quán đông khách du lịch, rating 4.8.", lat=21.0331, lng=105.8514, intensity=0.82, metadata={"category": "bun cha", "rating": 4.8, "eta_minutes": 18}),
    MapMarker(id="res_hn_002", type="restaurant", title="Phở Gà Cầu Giấy", description="Phù hợp đơn sáng và trưa, rating 4.6.", lat=21.0356, lng=105.7933, intensity=0.68, metadata={"category": "pho", "rating": 4.6, "eta_minutes": 17}),
]

DEMAND_MARKERS = [
    MapMarker(id="dem_hcm_001", type="demand", title="Điểm đông khách Bến Thành", description="Nhu cầu gọi xe cao do khách du lịch và trung chuyển.", lat=10.7726, lng=106.6980, intensity=0.9, metadata={"orders_last_15m": 42}),
    MapMarker(id="dem_hcm_002", type="demand", title="Điểm đông khách Vincom Đồng Khởi", description="Nhu cầu cao sau giờ mua sắm và tan ca.", lat=10.7780, lng=106.7016, intensity=0.76, metadata={"orders_last_15m": 31}),
    MapMarker(id="dem_hcm_003", type="demand", title="Điểm đông khách Thảo Điền", description="Nhu cầu tăng vào buổi tối quanh nhà hàng.", lat=10.8038, lng=106.7344, intensity=0.7, metadata={"orders_last_15m": 24}),
    MapMarker(id="dem_hn_001", type="demand", title="Điểm đông khách Hồ Gươm", description="Nhu cầu cao quanh phố đi bộ và khách sạn.", lat=21.0287, lng=105.8521, intensity=0.88, metadata={"orders_last_15m": 39}),
    MapMarker(id="dem_hn_002", type="demand", title="Điểm đông khách Lotte Đào Tấn", description="Nhu cầu tăng vào khung giờ tan sở.", lat=21.0322, lng=105.8124, intensity=0.73, metadata={"orders_last_15m": 27}),
]

TRAFFIC_MARKERS = [
    MapMarker(id="trf_hcm_001", type="traffic", title="Ùn nhẹ Nam Kỳ Khởi Nghĩa", description="Tốc độ giảm 35%, nên né giờ cao điểm.", lat=10.7831, lng=106.6923, intensity=0.64, metadata={"delay_minutes": 8}),
    MapMarker(id="trf_hcm_002", type="traffic", title="Kẹt xe Điện Biên Phủ", description="Ùn tại nút giao lớn, ưu tiên lộ trình song song.", lat=10.8013, lng=106.7140, intensity=0.78, metadata={"delay_minutes": 13}),
    MapMarker(id="trf_hn_001", type="traffic", title="Ùn nhẹ Tràng Tiền", description="Lượng xe cao quanh khu trung tâm.", lat=21.0253, lng=105.8540, intensity=0.62, metadata={"delay_minutes": 7}),
    MapMarker(id="trf_hn_002", type="traffic", title="Kẹt xe Nguyễn Chí Thanh", description="Nút giao đông, nên cân nhắc đường thay thế.", lat=21.0239, lng=105.8097, intensity=0.8, metadata={"delay_minutes": 14}),
]

ZONES = [
    MapZone(id="zone_hcm_demand_1", type="demand", title="Vùng cầu cao Quận 1", description="Heatmap: khách gọi xe và đặt đồ ăn tập trung.", center=GeoPoint(lat=10.7755, lng=106.7010), radius_m=900, intensity=0.86, metadata={"best_for": "driver_waiting"}),
    MapZone(id="zone_hcm_driver_1", type="driver_density", title="Vùng đông tài xế trung tâm", description="Nguồn cung tài xế dày, khách dễ gọi được xe nhanh.", center=GeoPoint(lat=10.7738, lng=106.6997), radius_m=750, intensity=0.78, metadata={"drivers": 36}),
    MapZone(id="zone_hcm_traffic_1", type="traffic", title="Vùng tắc Điện Biên Phủ", description="Tắc mức trung bình-cao.", center=GeoPoint(lat=10.8007, lng=106.7135), radius_m=650, intensity=0.75, metadata={"delay_minutes": 13}),
    MapZone(id="zone_hn_demand_1", type="demand", title="Vùng cầu cao Hồ Gươm", description="Khách du lịch, văn phòng và khách sạn tạo nhu cầu cao.", center=GeoPoint(lat=21.0292, lng=105.8504), radius_m=850, intensity=0.84, metadata={"best_for": "driver_waiting"}),
    MapZone(id="zone_hn_demand_2", type="demand", title="Nhu cầu ăn trưa Thanh Xuân", description="Khu vực tập trung nhiều văn phòng, nhu cầu gọi đồ ăn và xe rất cao.", center=GeoPoint(lat=20.9937, lng=105.8055), radius_m=900, intensity=0.79, metadata={"best_for": "driver_waiting"}),
    MapZone(id="zone_hn_traffic_1", type="traffic", title="Vùng tắc Nguyễn Chí Thanh", description="Tắc mức cao vào giờ tan sở.", center=GeoPoint(lat=21.0241, lng=105.8100), radius_m=700, intensity=0.8, metadata={"delay_minutes": 14}),
]

ROUTES = [
    MapRouteHint(id="rt_hcm_001", title="Đường tắt né Điện Biên Phủ", description="Gợi ý: rẽ qua Nguyễn Đình Chiểu để tránh đoạn ùn.", points=[GeoPoint(lat=10.8013, lng=106.7140), GeoPoint(lat=10.7950, lng=106.7077), GeoPoint(lat=10.7868, lng=106.7012)], eta_saving_minutes=7, metadata={"confidence": 0.68}),
    MapRouteHint(id="rt_hcm_002", title="Lối ra nhanh khỏi Bến Thành", description="Gợi ý: đi Lê Thánh Tôn thay vì vòng qua chợ khi đông.", points=[GeoPoint(lat=10.7726, lng=106.6980), GeoPoint(lat=10.7751, lng=106.7004), GeoPoint(lat=10.7788, lng=106.7040)], eta_saving_minutes=5, metadata={"confidence": 0.62}),
    MapRouteHint(id="rt_hn_001", title="Đường tắt né Tràng Tiền", description="Gợi ý: đi Hai Bà Trưng khi quanh Hồ Gươm đông.", points=[GeoPoint(lat=21.0253, lng=105.8540), GeoPoint(lat=21.0227, lng=105.8508), GeoPoint(lat=21.0204, lng=105.8465)], eta_saving_minutes=6, metadata={"confidence": 0.65}),
    MapRouteHint(id="rt_hn_002", title="Lối né Nguyễn Chí Thanh", description="Gợi ý: cân nhắc Kim Mã - Liễu Giai tùy hướng đón khách.", points=[GeoPoint(lat=21.0239, lng=105.8097), GeoPoint(lat=21.0304, lng=105.8121), GeoPoint(lat=21.0345, lng=105.8167)], eta_saving_minutes=8, metadata={"confidence": 0.66}),
]
