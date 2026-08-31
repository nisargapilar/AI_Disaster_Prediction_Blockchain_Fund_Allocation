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

  const isPrediction =
    mode === "prediction";

  const ring = active
    ? "box-shadow:0 0 0 5px rgba(255,255,255,0.18),0 0 12px ${color};"
    : `box-shadow:0 0 8px ${color};`;

  const border = isPrediction
    ? "border:2px dashed rgba(255,255,255,0.9);"
    : "border:2px solid rgba(255,255,255,0.65);";

  return L.divIcon({
    className: "",
    html: `
      <div
        style="
          width:16px;
          height:16px;
          border-radius:50%;
          background:${color};
          ${border}
          ${ring}
          cursor:pointer;
        "
      ></div>
    `,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
    popupAnchor: [0, -8],
  });
}

// ============================================================
// MOVE MAP TO SELECTED MARKER
// ============================================================

function FlyToSelected({ point }) {
  const map = useMap();

  useEffect(() => {
    if (!point) return;

    map.flyTo(
      [point.lat, point.lon],
      Math.max(map.getZoom(), 4),
      {
        duration: 0.6,
      }
    );
  }, [point, map]);

  return null;
}

// ============================================================
// FIT ALL POINTS ON MAP
// ============================================================

function FitAllPoints({ points }) {
  const map = useMap();

  useEffect(() => {
    if (!points || points.length === 0) return;

    if (points.length === 1) {
      map.setView(
        [points[0].lat, points[0].lon],
        5
      );
      return;
    }

    const bounds = L.latLngBounds(
      points.map((p) => [
        p.lat,
        p.lon,
      ])
    );

    map.fitBounds(bounds, {
      padding: [40, 40],
      maxZoom: 6,
    });
  }, [points, map]);

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
  // ----------------------------------------------------------
  // VALID POINTS
  // ----------------------------------------------------------

  const validPoints = points.filter(
    (p) =>
      typeof p.lat === "number" &&
      typeof p.lon === "number" &&
      Number.isFinite(p.lat) &&
      Number.isFinite(p.lon)
  );

  // ----------------------------------------------------------
  // REMOVE DUPLICATE REGION MARKERS
  //
  // If backend sends many records for Digha,
  // only the latest/first point for Digha is shown.
  // ----------------------------------------------------------

  const uniquePoints = [];

  const seenRegions = new Set();

  for (const point of validPoints) {
    const regionKey = String(
      point.region ||
        point.name ||
        `${point.lat}_${point.lon}`
    ).toLowerCase();

    if (seenRegions.has(regionKey)) {
      continue;
    }

    seenRegions.add(regionKey);
    uniquePoints.push(point);
  }

  // ----------------------------------------------------------
  // SELECTED POINT
  // ----------------------------------------------------------

  const selectedPoint =
    uniquePoints.find(
      (p) => p.id === selectedId
    );

  return (
    <div className="relative w-full aspect-[16/10] rounded overflow-hidden border border-white/5">

      <MapContainer
        center={[20, 78]}
        zoom={4}
        minZoom={3}
        maxZoom={12}
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
            ALL MARKERS
        ================================================== */}

        {uniquePoints.map((p) => (
          <Marker
            key={`${p.id}-${p.region}`}
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
                  fontFamily:
                    "monospace",
                  fontSize: "12px",
                  lineHeight: "1.6",
                  minWidth: "170px",
                }}
              >

                <strong
                  style={{
                    fontSize: "14px",
                  }}
                >
                  {p.name ||
                    p.region ||
                    "Unknown"}
                </strong>

                <br />

                <span>
                  Severity:{" "}
                  <b>
                    {p.severity ||
                      "Unknown"}
                  </b>
                </span>

                <br />

                <span>
                  Risk:{" "}
                  {p.riskPct !==
                  undefined
                    ? `${p.riskPct}%`
                    : p.riskScore !==
                        undefined
                      ? p.riskScore
                      : "—"}
                </span>

                <br />

                <span>
                  Latitude:{" "}
                  {Number(
                    p.lat
                  ).toFixed(4)}
                </span>

                <br />

                <span>
                  Longitude:{" "}
                  {Number(
                    p.lon
                  ).toFixed(4)}
                </span>

                {p.wind !==
                  undefined &&
                  p.wind !== null && (
                    <>
                      <br />
                      <span>
                        Wind:{" "}
                        {p.wind}
                      </span>
                    </>
                  )}

                {p.pressure !==
                  undefined &&
                  p.pressure !== null && (
                    <>
                      <br />
                      <span>
                        Pressure:{" "}
                        {p.pressure}
                      </span>
                    </>
                  )}

                {p.source && (
                  <>
                    <br />
                    <span>
                      Source:{" "}
                      {p.source}
                    </span>
                  </>
                )}

              </div>

            </Popup>

          </Marker>
        ))}

        {/* ==================================================
            FIT ALL DETECTION/PREDICTION POINTS
        ================================================== */}

        <FitAllPoints
          points={uniquePoints}
        />

        {/* ==================================================
            MOVE TO SELECTED POINT
        ================================================== */}

        <FlyToSelected
          point={selectedPoint}
        />

      </MapContainer>

      {/* ====================================================
          SEVERITY LEGEND
      ==================================================== */}

      <div className="pointer-events-none absolute bottom-2 left-3 flex items-center gap-3 text-[9px] font-mono uppercase tracking-widest text-slate-400 bg-black/60 px-2 py-1 rounded z-[1000]">

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
          MARKER COUNT
      ==================================================== */}

      <div className="pointer-events-none absolute top-2 left-3 text-[9px] font-mono uppercase tracking-widest text-slate-300 bg-black/60 px-2 py-1 rounded z-[1000]">

        {uniquePoints.length} LOCATION
        {uniquePoints.length === 1
          ? ""
          : "S"}

      </div>

      {/* ====================================================
          MODE INDICATOR
      ==================================================== */}

      <div className="pointer-events-none absolute top-2 right-3 text-[9px] font-mono uppercase tracking-widest text-slate-400 bg-black/60 px-2 py-1 rounded z-[1000]">

        {mode === "detection"
          ? "SOLID // VERIFIED FEED"
          : "DASHED // FORECAST ONLY"}

      </div>

    </div>
  );
}