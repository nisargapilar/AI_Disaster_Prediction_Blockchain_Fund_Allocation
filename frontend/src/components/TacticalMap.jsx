import { sevColors } from "../theme/ThemeContext";

// This panel is intentionally always dark, in both app themes — a radar
// screen doesn't get a "light mode." Swap this out for a real react-leaflet
// MapContainer later; keep the marker/severity styling.
export default function TacticalMap({ points, selectedId, onSelect, mode = "detection" }) {
  return (
    <div className="relative w-full aspect-[16/10] rounded bg-[#050810] border border-white/5 overflow-hidden">
      <div
        className="absolute inset-0 opacity-[0.15]"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(34,211,238,0.4) 1px, transparent 1px), linear-gradient(to bottom, rgba(34,211,238,0.4) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_75%_50%,rgba(34,211,238,0.08),transparent_60%)]" />
      <svg viewBox="0 0 100 60" preserveAspectRatio="none" className="absolute inset-0 w-full h-full opacity-[0.12]">
        <path d="M60 10 Q75 5 85 15 Q95 25 88 35 Q92 45 80 50 Q68 58 55 50 Q45 45 50 35 Q40 28 48 20 Q52 12 60 10 Z" fill="rgb(148 163 184)" />
      </svg>

      {points.map((p) => {
        const c = sevColors("dark")[p.severity] ?? sevColors("dark").low;
        const active = p.id === selectedId;
        return (
          <button
            key={p.id}
            onClick={() => onSelect(p.id)}
            className="absolute -translate-x-1/2 -translate-y-1/2 group"
            style={{ left: `${p.x}%`, top: `${p.y}%` }}
          >
            <span
              className={`block w-3.5 h-3.5 rounded-full ${c.dot} ${mode === "prediction" ? "opacity-70" : ""} ${
                active ? "ring-2 ring-offset-2 ring-offset-[#050810] ring-white/60" : ""
              }`}
              style={{
                boxShadow: active ? `0 0 0 6px rgba(255,255,255,0.06)` : undefined,
                border: mode === "prediction" ? "1.5px dashed rgba(255,255,255,0.6)" : "none",
              }}
            />
            <span className="absolute w-3.5 h-3.5 rounded-full animate-ping opacity-40" style={{ background: "currentColor" }} />
            <span className={`absolute top-5 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] font-mono px-1.5 py-0.5 rounded bg-black/80 border border-white/10 opacity-0 group-hover:opacity-100 transition-opacity ${mode === "detection" ? "text-cyan-300" : "text-violet-300"}`}>
              {p.id}
            </span>
          </button>
        );
      })}

      <div className="absolute bottom-2 left-3 flex items-center gap-3 text-[9px] font-mono uppercase tracking-widest text-slate-500">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400" />Low</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400" />Medium</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-400" />High</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-400" />Critical</span>
      </div>
      <div className="absolute top-2 right-3 text-[9px] font-mono uppercase tracking-widest text-slate-600">
        {mode === "detection" ? "SOLID // VERIFIED FEED" : "DASHED // FORECAST ONLY"}
      </div>
    </div>
  );
}