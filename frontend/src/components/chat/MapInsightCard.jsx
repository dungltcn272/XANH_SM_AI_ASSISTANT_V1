import React, { useMemo, useState, useEffect, useRef } from 'react';
import { Circle, Layers, MapPin, Navigation, Route, Store, TrafficCone, Users } from 'lucide-react';
import { Circle as LeafletCircle, MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { api } from '../../api';

// Removed CSS transition for vehicle-marker to avoid panning lag

const MapFitter = ({ markers, zones, routes }) => {
  const map = useMap();

  useEffect(() => {
    const bounds = L.latLngBounds();
    let hasPoints = false;

    if (markers?.length > 0) {
      markers.forEach(m => bounds.extend([m.lat, m.lng]));
      hasPoints = true;
    }
    
    if (zones?.length > 0) {
      zones.forEach(z => {
        const center = L.latLng(z.center.lat, z.center.lng);
        // Estimate radius in degrees (~111km per degree)
        const radiusDeg = z.radius_m / 111000;
        bounds.extend([center.lat + radiusDeg, center.lng + radiusDeg]);
        bounds.extend([center.lat - radiusDeg, center.lng - radiusDeg]);
      });
      hasPoints = true;
    }
    
    if (routes?.length > 0) {
      routes.forEach(r => {
        if (r.points?.length > 0) {
          r.points.forEach(p => bounds.extend([p.lat, p.lng]));
        }
      });
      hasPoints = true;
    }

    if (hasPoints) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
    }
  }, [map, markers, zones, routes]);

  return null;
};

// Smoothly interpolates lat/lng without using CSS transition on Leaflet container
const AnimatedMarker = ({ position, icon, children }) => {
  const markerRef = useRef(null);
  const animRef = useRef(null);
  const [initialPos] = useState(position);

    const lat = position[0];
    const lng = position[1];

    useEffect(() => {
    if (markerRef.current) {
      const marker = markerRef.current;
      const startLatLng = marker.getLatLng();
      const endLatLng = L.latLng(lat, lng);
      
      if (startLatLng.distanceTo(endLatLng) > 5000) {
        marker.setLatLng(endLatLng);
        return;
      }

      if (startLatLng.equals(endLatLng)) return;
      if (animRef.current) cancelAnimationFrame(animRef.current);
      
      let startTime = null;
      const duration = 2000;

      const animate = (timestamp) => {
        if (!startTime) startTime = timestamp;
        const progress = Math.min((timestamp - startTime) / duration, 1);
        
        const currentLat = startLatLng.lat + (endLatLng.lat - startLatLng.lat) * progress;
        const currentLng = startLatLng.lng + (endLatLng.lng - startLatLng.lng) * progress;
        
        marker.setLatLng([currentLat, currentLng]);

        if (progress < 1) {
          animRef.current = requestAnimationFrame(animate);
        }
      };
      
      animRef.current = requestAnimationFrame(animate);
    }
    
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [lat, lng]);

  return <Marker ref={markerRef} position={initialPos} icon={icon}>{children}</Marker>;
};

const LAYER_META = {
  drivers: { label: 'Tài xế', color: '#00a884', icon: Users },
  restaurants: { label: 'Quán ăn', color: '#f97316', icon: Store },
  demand: { label: 'Đông khách', color: '#2563eb', icon: Circle },
  traffic: { label: 'Tắc đường', color: '#ef4444', icon: TrafficCone },
  shortcuts: { label: 'Đường tắt', color: '#7c3aed', icon: Route },
  start: { label: 'Điểm đi', color: '#10b981', icon: MapPin },
  end: { label: 'Điểm đến', color: '#ef4444', icon: MapPin },
};

const markerColor = (type) => {
  if (type === 'driver') return LAYER_META.drivers.color;
  if (type === 'restaurant') return LAYER_META.restaurants.color;
  if (type === 'traffic') return LAYER_META.traffic.color;
  if (type === 'demand') return LAYER_META.demand.color;
  if (type === 'start') return LAYER_META.start.color;
  if (type === 'end') return LAYER_META.end.color;
  return '#3b82f6';
};

const markerIcon = (type, intensity = 0.5) => L.divIcon({
  className: '',
  html: `<div style="width:${22 + intensity * 10}px;height:${22 + intensity * 10}px;border-radius:9999px;background:${markerColor(type)};border:3px solid white;box-shadow:0 10px 24px rgba(0,0,0,.24);"></div>`,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const vehicleIcon = (type, status, heading) => {
  const imgUrl = type === 'bike' ? '/bike.png' : '/car.png';
  const indicatorColor = status === 'available' ? '#10b981' : '#ef4444';
  
  return L.divIcon({
    className: 'vehicle-marker',
    html: `
      <div style="position:relative; width:36px; height:36px; transform: rotate(${heading}deg); transition: transform 0.5s ease-out;">
        <img src="${imgUrl}" style="width:100%; height:100%; object-fit:contain; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));" />
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); width:10px; height:10px; border-radius:50%; background:${indicatorColor}; border:2px solid white; box-shadow:0 0 4px rgba(0,0,0,0.3);"></div>
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
};

const zoneColor = (type) => {
  if (type === 'traffic') return LAYER_META.traffic.color;
  if (type === 'driver_density') return LAYER_META.drivers.color;
  return LAYER_META.demand.color;
};

const zoneLayer = (type) => {
  if (type === 'traffic') return 'traffic';
  if (type === 'driver_density') return 'drivers';
  return 'demand';
};

const markerLayer = (type) => {
  if (type === 'driver') return 'drivers';
  if (type === 'restaurant') return 'restaurants';
  if (type === 'traffic') return 'traffic';
  return 'demand';
};

export const MapInsightCard = ({ payload }) => {
  const initialLayers = (payload?.layers && payload.layers.length > 0) ? payload.layers : Object.keys(LAYER_META);
  const [visibleLayers, setVisibleLayers] = useState(() => new Set(initialLayers));
  const center = useMemo(() => [Number(payload?.center?.lat) || 10.7769, Number(payload?.center?.lng) || 106.7009], [payload?.center?.lat, payload?.center?.lng]);
  const [realtimeVehicles, setRealtimeVehicles] = useState([]);

  // Fetch realtime vehicles
  useEffect(() => {
    let mounted = true;
    const fetchVehicles = async () => {
      try {
        let qLat1 = center[0], qLng1 = center[1], qLat2 = null, qLng2 = null;
        if (payload?.routes && payload.routes.length > 0 && payload.routes[0].points.length > 0) {
           const pts = payload.routes[0].points;
           qLat1 = pts[0].lat;
           qLng1 = pts[0].lng;
           qLat2 = pts[pts.length - 1].lat;
           qLng2 = pts[pts.length - 1].lng;
        }
        
        const res = await api.getMapRealtimeVehicles(qLat1, qLng1, 3.0, qLat2, qLng2);
        if (mounted && res.success) {
          setRealtimeVehicles(res.drivers);
        }
      } catch (err) {
        console.error("Error fetching vehicles:", err);
      }
    };

    fetchVehicles();
    const interval = setInterval(fetchVehicles, 2000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [center, payload?.routes]);

  const markers = useMemo(
    () => (payload?.markers || []).filter((item) => visibleLayers.has(markerLayer(item.type))),
    [payload?.markers, visibleLayers]
  );
  const zones = useMemo(
    () => (payload?.zones || []).filter((item) => visibleLayers.has(zoneLayer(item.type))),
    [payload?.zones, visibleLayers]
  );
  const displayRoutes = useMemo(
    () => (payload?.routes || []).filter(r => {
       if (r.type === 'traffic') return visibleLayers.has('traffic');
       return visibleLayers.has('shortcuts'); 
    }),
    [payload?.routes, visibleLayers]
  );

  if (!payload) return null;

  const toggleLayer = (layer) => {
    setVisibleLayers((prev) => {
      const next = new Set(prev);
      if (next.has(layer)) next.delete(layer);
      else next.add(layer);
      return next;
    });
  };

  return (
    <div className="w-full overflow-hidden rounded-2xl md:rounded-3xl border border-white/50 dark:border-white/10 bg-white/76 dark:bg-white/[0.04] shadow-[0_12px_40px_rgba(0,0,0,0.06)]">
      <div className="p-3 md:p-4 border-b border-outline-variant/15 flex flex-col gap-3">
        <div className="flex items-start gap-2.5">
          <div className="w-9 h-9 rounded-full bg-[#00c897]/12 text-[#009e79] flex items-center justify-center shrink-0">
            <MapPin size={18} />
          </div>
          <div className="min-w-0">
            <h3 className="text-base md:text-xl font-black text-on-surface leading-tight">Bản đồ trực tuyến</h3>
            <p className="mt-1 text-xs md:text-sm text-on-surface-variant/85 leading-relaxed">
              Dữ liệu được cập nhật từ hệ thống vệ tinh và điều hướng trực tuyến.
            </p>
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto no-scrollbar">
          {Object.entries(LAYER_META).map(([layer, meta]) => {
            const Icon = meta.icon;
            const active = visibleLayers.has(layer);
            return (
              <button
                key={layer}
                type="button"
                onClick={() => toggleLayer(layer)}
                className={`h-9 shrink-0 rounded-full border px-3 text-xs font-black inline-flex items-center gap-1.5 transition-colors ${
                  active
                    ? 'bg-[#00c897]/10 border-[#00c897]/30 text-[#008f6f]'
                    : 'border-outline-variant/25 text-on-surface-variant/70 hover:bg-surface-container-high/60'
                }`}
              >
                <Icon size={14} color={active ? meta.color : 'currentColor'} />
                {meta.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="h-[320px] md:h-[420px] w-full relative">
        <MapContainer center={center} zoom={14} className="w-full h-full z-0 relative font-sans" zoomControl={false}>
          <MapFitter markers={markers} zones={zones} routes={displayRoutes} />
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          />
          {zones.map((zone) => (
            <LeafletCircle
              key={zone.id}
              center={[zone.center.lat, zone.center.lng]}
              radius={zone.radius_m}
              pathOptions={{
                color: zoneColor(zone.type),
                fillColor: zoneColor(zone.type),
                fillOpacity: 0.12 + (zone.intensity || 0.5) * 0.14,
                weight: 2,
              }}
            >
              <Popup>
                <strong>{zone.title}</strong>
                <br />
                {zone.description}
              </Popup>
            </LeafletCircle>
          ))}

          {displayRoutes.map((route, idx) => {
            const color = route.type === 'traffic' ? '#ef4444' : ['#3b82f6', '#10b981', '#f59e0b'][idx % 3];
            const weight = route.type === 'traffic' ? 8 : 6;
            const pts = route.points || [];
            const start = pts[0];
            const end = pts[pts.length - 1];
            return (
              <React.Fragment key={route.id}>
                <Polyline
                  positions={pts.map((point) => [point.lat, point.lng])}
                  pathOptions={{ color: color, weight: weight, opacity: 0.8 }}
                >
                  <Popup>
                    <strong>{route.title}</strong>
                    <br />
                    {route.description}
                    {route.eta_saving_minutes ? <><br />Tiết kiệm khoảng {route.eta_saving_minutes} phút</> : null}
                  </Popup>
                </Polyline>
                
                {/* Arrow at 50% of the route */}
                {route.type !== 'traffic' && pts.length > 3 && (
                  <Marker 
                    position={[pts[Math.floor(pts.length / 2)].lat, pts[Math.floor(pts.length / 2)].lng]} 
                    icon={L.divIcon({
                      className: 'route-arrow',
                      html: `<svg style="transform: rotate(${Math.atan2(pts[Math.floor(pts.length / 2) + 1].lng - pts[Math.floor(pts.length / 2) - 1].lng, pts[Math.floor(pts.length / 2) + 1].lat - pts[Math.floor(pts.length / 2) - 1].lat) * 180 / Math.PI}deg); width: 24px; height: 24px;" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"></path><path d="m12 5 7 7-7 7"></path></svg>`,
                      iconSize: [24, 24],
                      iconAnchor: [12, 12]
                    })}
                  />
                )}
                
                {/* Fallback circles if marker is missing */}
                {route.type !== 'traffic' && start && !payload?.markers?.some(m => m.lat === start.lat) && (
                  <LeafletCircle center={[start.lat, start.lng]} radius={45} pathOptions={{ color: 'white', fillColor: '#10b981', fillOpacity: 1, weight: 3 }}>
                    <Popup>Điểm xuất phát</Popup>
                  </LeafletCircle>
                )}
                {route.type !== 'traffic' && end && !payload?.markers?.some(m => m.lat === end.lat) && (
                  <LeafletCircle center={[end.lat, end.lng]} radius={45} pathOptions={{ color: 'white', fillColor: '#ef4444', fillOpacity: 1, weight: 3 }}>
                    <Popup>Điểm đến</Popup>
                  </LeafletCircle>
                )}
              </React.Fragment>
            );
          })}

          {markers.map((marker) => (
            <Marker key={marker.id} position={[marker.lat, marker.lng]} icon={markerIcon(marker.type, marker.intensity)}>
              <Popup>
                <strong>{marker.title}</strong>
                <br />
                {marker.description}
                {marker.metadata?.distance_km ? <><br />Cách tâm bản đồ {marker.metadata.distance_km} km</> : null}
              </Popup>
            </Marker>
          ))}

          {/* Render Realtime Vehicles */}
          {visibleLayers.has('drivers') && realtimeVehicles.map((vehicle) => (
            <AnimatedMarker 
              key={vehicle.driver_id} 
              position={[vehicle.lat, vehicle.lng]} 
              icon={vehicleIcon(vehicle.vehicle_type, vehicle.status, vehicle.heading)}
            >
              <Popup>
                <strong>{vehicle.driver_id} - {vehicle.vehicle_type === 'bike' ? 'Xanh Bike' : 'Xanh Car'}</strong>
                <br />
                Trạng thái: {vehicle.status === 'available' ? 'Đang rảnh' : 'Đang có khách'}
                <br />
                Đánh giá: ⭐ {vehicle.rating}
                <br />
                Tốc độ: {vehicle.speed} km/h
              </Popup>
            </AnimatedMarker>
          ))}
        </MapContainer>
      </div>

      <div className="p-3 md:p-4 border-t border-outline-variant/15 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
        <div className="rounded-xl bg-surface-container-high/50 p-2 font-bold text-on-surface-variant">
          <Layers size={14} className="inline mr-1 text-[#00a884]" />
          {payload.layers?.length || 0} lớp dữ liệu
        </div>
        <div className="rounded-xl bg-surface-container-high/50 p-2 font-bold text-on-surface-variant">
          <MapPin size={14} className="inline mr-1 text-[#00a884]" />
          {payload.markers?.length || 0} điểm
        </div>
        <div className="rounded-xl bg-surface-container-high/50 p-2 font-bold text-on-surface-variant">
          <Circle size={14} className="inline mr-1 text-[#2563eb]" />
          {payload.zones?.length || 0} vùng
        </div>
        <div className="rounded-xl bg-surface-container-high/50 p-2 font-bold text-on-surface-variant">
          <Navigation size={14} className="inline mr-1 text-[#7c3aed]" />
          {payload.routes?.length || 0} tuyến
        </div>
      </div>
    </div>
  );
};
