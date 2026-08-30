import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import { useEffect } from "react";

// ============================================================
// SEVERITY COLORS
// Works for Earthquake, Flood and Forest Fire
// ============================================================

const SEV_COLOR = {
  low: "#34d399",
  medium: "#fbbf24",
  high: "#fb923c",
  critical: "#fb7185",
};

// ============================================================
// WORLD BOUNDS
// ============================================================

const WORLD_BOUNDS = [
  [-90, -180],
  [90, 180],
];

// ============================================================
// MARKER ICON
// ============================================================

function makeIcon(severity, mode, active) {
  const normalizedSeverity = String(
    severity || "low"
  ).toLowerCase();

  const color =
    SEV_COLOR[normalizedSeverity] ||
    SEV_COLOR.low;

  const dashed = mode === "prediction";

  const ring = active
    ? "box-shadow:0 0 0 5px rgba(255,255,255,0.15);"
    : "";

  const border = dashed
    ? "border:2px dashed rgba(255,255,255,0.85);"
    : "border:2px solid rgba(255,255,255,0.5);";

  return L.divIcon({
    className: "",
    html: `
      <div
        style="
          width:14px;
          height:14px;
          border-radius:50%;
          background:${color};
          ${border}
          ${ring}
        "
      ></div>
    `,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

// ============================================================
// MOVE MAP TO SELECTED MARKER
// ============================================================

function FlyToSelected({ point }) {
  const map = useMap();

  useEffect(() => {
    if (point) {
      map.flyTo(
        [point.lat, point.lon],
        Math.max(map.getZoom(), 4),
        {
          duration: 0.6,
        }
      );
    }
  }, [point, map]);

  return null;
}

// ============================================================
// REAL MAP
// ============================================================

export default function RealMap({
  points = [],
  selectedId,
  onSelect,
  mode = "detection",
}) {
  const selectedPoint = points.find(
    (p) => p.id === selectedId
  );

  return (
    <div className="relative w-full aspect-[16/10] rounded overflow-hidden border border-white/5">

      <MapContainer
        center={[20, 0]}
        zoom={2}
        minZoom={3}
        maxBounds={WORLD_BOUNDS}
        maxBoundsViscosity={1.0}
        style={{
          height: "100%",
          width: "100%",
          background: "#050810",
        }}
      >

        {/* ==================================================
            MAP TILES
        ================================================== */}

        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.de/{z}/{x}/{y}.png"
          noWrap
          bounds={WORLD_BOUNDS}
        />

        {/* ==================================================
            EARTHQUAKE / FLOOD / FOREST FIRE MARKERS
        ================================================== */}

        {points
          .filter(
            (p) =>
              typeof p.lat === "number" &&
              typeof p.lon === "number"
          )
          .map((p) => (
            <Marker
              key={p.id}
              position={[
                p.lat,
                p.lon,
              ]}
              icon={makeIcon(
                p.severity,
                mode,
                p.id === selectedId
              )}
              eventHandlers={{
                click: () => {
                  if (onSelect) {
                    onSelect(p.id);
                  }
                },
              }}
            >

              <Popup>
                <div
                  style={{
                    fontFamily: "monospace",
                    fontSize: "12px",
                  }}
                >

                  <strong>
                    {p.name ||
                      p.region ||
                      p.id}
                  </strong>

                  <br />

                  Severity:{" "}
                  {p.severity ||
                    "Unknown"}

                  <br />

                  Latitude:{" "}
                  {Number(
                    p.lat
                  ).toFixed(3)}

                  <br />

                  Longitude:{" "}
                  {Number(
                    p.lon
                  ).toFixed(3)}

                </div>
              </Popup>

            </Marker>
          ))}

        {/* ==================================================
            SELECTED MARKER
        ================================================== */}

        <FlyToSelected
          point={selectedPoint}
        />

      </MapContainer>

      {/* ====================================================
          SEVERITY LEGEND
      ==================================================== */}

      <div className="pointer-events-none absolute bottom-2 left-3 flex items-center gap-3 text-[9px] font-mono uppercase tracking-widest text-slate-400 bg-black/50 px-2 py-1 rounded z-[1000]">

        <span className="flex items-center gap-1">
          <span
            className="w-2 h-2 rounded-full"
            style={{
              background:
                SEV_COLOR.low,
            }}
          />
          Low
        </span>

        <span className="flex items-center gap-1">
          <span
            className="w-2 h-2 rounded-full"
            style={{
              background:
                SEV_COLOR.medium,
            }}
          />
          Medium
        </span>

        <span className="flex items-center gap-1">
          <span
            className="w-2 h-2 rounded-full"
            style={{
              background:
                SEV_COLOR.high,
            }}
          />
          High
        </span>

        <span className="flex items-center gap-1">
          <span
            className="w-2 h-2 rounded-full"
            style={{
              background:
                SEV_COLOR.critical,
            }}
          />
          Critical
        </span>

      </div>

      {/* ====================================================
          MODE INDICATOR
      ==================================================== */}

      <div className="pointer-events-none absolute top-2 right-3 text-[9px] font-mono uppercase tracking-widest text-slate-400 bg-black/50 px-2 py-1 rounded z-[1000]">

        {mode === "detection"
          ? "SOLID // VERIFIED FEED"
          : "DASHED // FORECAST ONLY"}

      </div>

    </div>
  );
}