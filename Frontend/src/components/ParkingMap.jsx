import { useMemo } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

function clamp01(x) {
  if (x < 0) return 0;
  if (x > 1) return 1;
  return x;
}

function colorForGarage(g) {
  const cap = g.capacity ?? 0;
  const occ = g.occupied_now ?? 0;
  const util = cap > 0 ? clamp01(occ / cap) : 0;

  if (util < 0.5) return "#2e7d32";
  if (util < 0.8) return "#f9a825";
  return "#c62828";
}

function circleDivIcon(color, isSelected) {
  const size = isSelected ? 16 : 12;
  const ring = isSelected
    ? "2px solid rgba(255,255,255,0.9)"
    : "1px solid rgba(255,255,255,0.7)";
  return L.divIcon({
    className: "",
    html: `<div style="
      width:${size}px;height:${size}px;
      border-radius:999px;
      background:${color};
      border:${ring};
      box-shadow: 0 6px 16px rgba(0,0,0,0.35);
    "></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -10],
  });
}

export default function ParkingMap({ garages, selectedId, onSelect }) {
  const center = [43.0748, -89.3840];

  const markers = useMemo(() => {
    return (garages ?? []).map((g) => {
      const isSelected = g.garage_id === selectedId;
      const color = colorForGarage(g);
      const icon = circleDivIcon(color, isSelected);
      return { g, icon };
    });
  }, [garages, selectedId]);

  return (
    <div style={styles.wrap}>
      <MapContainer center={center} zoom={14} scrollWheelZoom style={styles.map}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {markers.map(({ g, icon }) => (
          <Marker
            key={g.garage_id}
            position={[g.lat, g.lng]}
            icon={icon}
            eventHandlers={{ click: () => onSelect?.(g.garage_id) }}
          >
            <Popup>
              <div style={{ minWidth: 220 }}>
                <div style={{ fontWeight: 700, marginBottom: 6 }}>{g.name}</div>
                <div style={styles.line}>
                  <span>Available now</span>
                  <strong>{g.available_now}</strong>
                </div>
                <div style={styles.line}>
                  <span>Occupied now</span>
                  <strong>{g.occupied_now}</strong>
                </div>
                <div style={styles.line}>
                  <span>Capacity</span>
                  <strong>{g.capacity ?? "—"}</strong>
                </div>
                <div style={styles.line}>
                  <span>Predicted (30 min)</span>
                  <strong>{g.predicted_30 ?? "—"}</strong>
                </div>
                <div style={{ marginTop: 8, opacity: 0.75, fontSize: 12 }}>
                  Updated: {g.updated_at ?? "—"}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}

const styles = {
  wrap: {
    borderRadius: 14,
    overflow: "hidden",
    border: "1px solid rgba(255,255,255,0.08)",
    background: "rgba(255,255,255,0.03)",
    width: "100%",
    maxWidth: "100%",
  },
  // IMPORTANT: avoid 100vh math inside a grid; use a stable responsive height
  map: {
    width: "100%",
    height: "72vh",
    minHeight: 520,
  },
  line: {
    display: "flex",
    justifyContent: "space-between",
    gap: 12,
    fontSize: 13,
    marginTop: 4,
  },
};
