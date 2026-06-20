import React, { useState, useEffect } from 'react';
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Search, MapPin, CheckCheck, LocateFixed } from 'lucide-react';

const foodPinIcon = L.divIcon({
  className: '',
  html: '<div style="width:28px;height:28px;border-radius:9999px;background:#00a884;border:3px solid white;box-shadow:0 8px 24px rgba(0,168,132,.35);"></div>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const FoodMapClickHandler = ({ onPick }) => {
  useMapEvents({
    click(event) {
      onPick({ lat: event.latlng.lat, lng: event.latlng.lng, label: 'Vị trí đã chọn trên bản đồ' });
    },
  });
  return null;
};

const FoodMapRecenter = ({ center }) => {
  const map = useMap();
  const [lat, lng] = center;

  useEffect(() => {
    map.setView([lat, lng], map.getZoom(), { animate: true });
  }, [map, lat, lng]);

  return null;
};

export const FoodMapPicker = ({ selectedPin, onPick, onConfirm, interactive = true, heightClass = 'h-56 md:h-64' }) => {
  const center = [
    Number(selectedPin?.lat) || 10.7769,
    Number(selectedPin?.lng) || 106.7009,
  ];

  return (
    <div className={`relative ${heightClass} overflow-hidden rounded-2xl border border-outline-variant/15 bg-surface-container-high`}>
      <MapContainer
        center={center}
        zoom={15}
        scrollWheelZoom={interactive}
        dragging={interactive}
        doubleClickZoom={interactive}
        className="h-full w-full z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FoodMapRecenter center={center} />
        {interactive && <FoodMapClickHandler onPick={onPick} />}
        <Marker position={center} icon={foodPinIcon} />
      </MapContainer>
      {interactive && (
        <button
          type="button"
          onClick={() => onConfirm?.(selectedPin)}
          className="absolute bottom-3 left-3 right-3 z-[500] h-11 rounded-xl bg-[#00a884] text-sm font-black text-white shadow-lg hover:bg-[#008f73] transition-colors"
        >
          Xác nhận vị trí đã chọn
        </button>
      )}
    </div>
  );
};

export const FoodLocationRequestCard = ({ request, onUseCurrentLocation, onSubmitAddress, onSelectMapLocation, savedLocations = [] }) => {
  const [address, setAddress] = useState('');
  const [mapMode, setMapMode] = useState(false);
  const [selectedPin, setSelectedPin] = useState({ lat: 10.7769, lng: 106.7009, label: 'Vị trí đã chọn trên bản đồ' });

  const submitAddress = (event) => {
    event.preventDefault();
    const trimmed = address.trim();
    if (!trimmed) return;
    onSubmitAddress(trimmed);
  };

  return (
    <div className="w-full">
      <div className="overflow-hidden rounded-3xl border border-outline-variant/20 bg-white/82 dark:bg-white/[0.04] shadow-[0_12px_40px_rgba(0,0,0,0.05)]">
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,0.95fr)_minmax(260px,1fr)] gap-4 p-4 md:p-5">
          <div className="flex flex-col justify-between gap-4">
            <div>
              <h3 className="text-lg md:text-xl font-black text-on-surface leading-snug">
                Để gợi ý món ăn gần bạn chính xác hơn, em cần biết vị trí hiện tại của bạn nhé!
              </h3>
              <p className="mt-3 text-sm md:text-base text-on-surface-variant/85 leading-relaxed">
                Em sẽ giúp bạn tìm quán gần nhất, ước tính thời gian giao hàng và tính phí ship chính xác.
              </p>
            </div>

            <div className="flex flex-col gap-2">
              <button
                type="button"
                onClick={onUseCurrentLocation}
                className="h-12 rounded-xl bg-[#00a884] px-4 text-sm md:text-base font-black text-white hover:bg-[#008f73] transition-colors inline-flex items-center justify-center gap-2"
              >
                <LocateFixed size={18} />
                {request?.current_location_label || 'Chia sẻ vị trí hiện tại'}
              </button>
              <button
                type="button"
                onClick={() => setMapMode(prev => !prev)}
                className="h-12 rounded-xl border border-[#00a884] px-4 text-sm md:text-base font-black text-[#008f6f] hover:bg-[#00c897]/10 transition-colors inline-flex items-center justify-center gap-2"
              >
                <MapPin size={18} />
                Chọn trên bản đồ
              </button>
            </div>
          </div>

          <div>
            <FoodMapPicker
              selectedPin={selectedPin}
              onPick={setSelectedPin}
              onConfirm={onSelectMapLocation}
              interactive={mapMode}
            />
            <div className="mt-2 text-xs text-on-surface-variant/75">
              Bạn có thể chia sẻ vị trí hiện tại hoặc chọn pin trên bản đồ
            </div>
          </div>
        </div>

        <form onSubmit={submitAddress} className="border-t border-outline-variant/15 p-4 md:p-5">
          <div className="flex flex-col sm:flex-row gap-2">
            <label className="relative flex-1">
              <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/50" />
              <input
                value={address}
                onChange={(event) => setAddress(event.target.value)}
                placeholder={request?.address_placeholder || 'Nhập địa chỉ giao hàng'}
                className="w-full h-12 rounded-xl border border-outline-variant/30 bg-white/85 dark:bg-white/5 pl-10 pr-3 text-sm font-semibold text-on-surface outline-none focus:border-[#00c897] focus:ring-2 focus:ring-[#00c897]/15 transition-all"
              />
            </label>
            <button
              type="submit"
              className="h-12 rounded-xl border border-[#00a884] px-4 text-sm font-black text-[#008f6f] hover:bg-[#00c897] hover:text-white transition-colors whitespace-nowrap"
            >
              {request?.submit_label || 'Tìm quán gần đây'}
            </button>
          </div>
          {savedLocations.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {savedLocations.slice(0, 3).map((place) => (
                <button
                  key={place.id}
                  type="button"
                  onClick={() => onSelectMapLocation(place)}
                  className="rounded-full border border-[#00a884]/30 bg-[#00c897]/8 px-3 py-1.5 text-xs font-bold text-[#008f6f] hover:bg-[#00c897]/15 transition-colors"
                >
                  {place.label}
                </button>
              ))}
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export const FoodLocationConfirmedCard = ({ location, onSaveNamedLocation }) => {
  if (!location) return null;
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[minmax(220px,0.8fr)_minmax(260px,1fr)] gap-4 rounded-3xl border border-[#00c897]/25 bg-white/82 dark:bg-white/[0.04] p-4 md:p-5 shadow-[0_12px_40px_rgba(0,0,0,0.05)]">
      <div className="flex flex-col justify-center gap-3">
        <div className="flex items-center gap-2 text-lg font-black text-on-surface">
          <span className="w-8 h-8 rounded-full bg-[#00a884] text-white flex items-center justify-center">
            <CheckCheck size={18} />
          </span>
          Vị trí hiện tại của bạn
        </div>
        <div className="text-sm leading-relaxed text-on-surface-variant/90">
          {location.label || location.address || 'Đã cập nhật vị trí giao hàng'}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => onSaveNamedLocation?.('home', 'Nhà', location)}
            className="rounded-full border border-[#00a884]/30 px-3 py-1.5 text-xs font-black text-[#008f6f] hover:bg-[#00c897]/10 transition-colors"
          >
            Lưu là Nhà
          </button>
          <button
            type="button"
            onClick={() => onSaveNamedLocation?.('work', 'Công ty', location)}
            className="rounded-full border border-[#00a884]/30 px-3 py-1.5 text-xs font-black text-[#008f6f] hover:bg-[#00c897]/10 transition-colors"
          >
            Lưu là Công ty
          </button>
        </div>
      </div>
      <FoodMapPicker
        selectedPin={{ lat: location.lat, lng: location.lng }}
        interactive={false}
        heightClass="h-40"
      />
    </div>
  );
};
