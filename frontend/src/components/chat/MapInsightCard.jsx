import React, { useMemo, useState, useEffect } from 'react';
import { Circle, Layers, MapPin, Navigation, Route, Store, TrafficCone, Users } from 'lucide-react';
import { Circle as LeafletCircle, MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const MapFitter = ({ markers, zones, routes }) => {
  const map = useMap();
  useEffect(() => {
    const bounds = L.latLngBounds();
    let hasData = false;
    markers.forEach(m => { bounds.extend([m.lat, m.lng]); hasData = true; });
    zones.forEach(z => { bounds.extend([z.center.lat, z.center.lng]); hasData = true; });
    routes.forEach(r => r.points.forEach(p => { bounds.extend([p.lat, p.lng]); hasData = true; }));
    
    if (hasData) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }
  }, [map, markers, zones, routes]);
  return null;
};

const LAYER_META = {
  drivers: { label: 'Tài xế', color: '#00a884', icon: Users },
  restaurants: { label: 'Quán ăn', color: '#f97316', icon: Store },
  demand: { label: 'Đông khách', color: '#2563eb', icon: Circle },
  traffic: { label: 'Tắc đường', color: '#ef4444', icon: TrafficCone },
  shortcuts: { label: 'Đường tắt', color: '#7c3aed', icon: Route },
};

const markerColor = (type) => {
  if (type === 'driver') return LAYER_META.drivers.color;
  if (type === 'restaurant') return LAYER_META.restaurants.color;
  if (type === 'demand') return LAYER_META.demand.color;
  if (type === 'traffic') return LAYER_META.traffic.color;
  return '#00a884';
};

const markerIcon = (type, intensity = 0.5) => L.divIcon({
  className: '',
  html: `<div style="width:${22 + intensity * 10}px;height:${22 + intensity * 10}px;border-radius:9999px;background:${markerColor(type)};border:3px solid white;box-shadow:0 10px 24px rgba(0,0,0,.24);"></div>`,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

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
  const center = [Number(payload?.center?.lat) || 10.7769, Number(payload?.center?.lng) || 106.7009];

  const markers = useMemo(
    () => (payload?.markers || []).filter((item) => visibleLayers.has(markerLayer(item.type))),
    [payload?.markers, visibleLayers]
  );
  const zones = useMemo(
    () => (payload?.zones || []).filter((item) => visibleLayers.has(zoneLayer(item.type))),
    [payload?.zones, visibleLayers]
  );
  const routes = useMemo(
    () => (payload?.routes || []).filter(() => visibleLayers.has('shortcuts')),
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
          <MapFitter markers={markers} zones={zones} routes={routes} />
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

          {routes.map((route, idx) => {
            const color = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'][idx % 4];
            const pts = route.points || [];
            const start = pts[0];
            const end = pts[pts.length - 1];
            return (
              <React.Fragment key={route.id}>
                <Polyline
                  positions={pts.map((point) => [point.lat, point.lng])}
                  pathOptions={{ color: color, weight: 6, opacity: 0.8 }}
                >
                  <Popup>
                    <strong>{route.title}</strong>
                    <br />
                    {route.description}
                    {route.eta_saving_minutes ? <><br />Tiết kiệm khoảng {route.eta_saving_minutes} phút</> : null}
                  </Popup>
                </Polyline>
                {start && (
                  <LeafletCircle center={[start.lat, start.lng]} radius={45} pathOptions={{ color: 'white', fillColor: '#10b981', fillOpacity: 1, weight: 3 }}>
                    <Popup>Điểm xuất phát</Popup>
                  </LeafletCircle>
                )}
                {end && (
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
