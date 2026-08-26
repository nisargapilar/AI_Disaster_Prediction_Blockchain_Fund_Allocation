import { Shield, Sun, Moon } from "lucide-react";
import { useTheme, surface, accentText } from "../theme/ThemeContext";
import { Badge, Clock24 } from "./ui";

export default function Navbar({ view, setView }) {
  const { theme, toggle } = useTheme();
  const s = surface(theme);
  const items = [
    { id: "dashboard", label: "Dashboard" },
    { id: "detect-select", label: "Detection" },
    { id: "predict-select", label: "Prediction" },
    { id: "funds", label: "Funds" },
  ];
  const isActive = (id) => {
    if (id === "detect-select")
      return view === "detect-select" || view === "eq-detection";
    if (id === "predict-select")
      return view === "predict-select" || view === "eq-prediction";
    return view === id;
  };

  return (
    <div className={`border-b border-cyan-400/20 ${s.nav}`}>
      <div className="flex items-center justify-between px-5 py-3">
        <button
          onClick={() => setView("dashboard")}
          className="flex items-center gap-2.5"
        >
          <div className="w-8 h-8 rounded bg-cyan-400/10 border border-cyan-400/40 flex items-center justify-center">
            <Shield className={`w-4 h-4 ${accentText(theme, "cyan")}`} />
          </div>
          <div className="text-left">
            <div className={`text-sm font-bold tracking-wide ${s.textPrimary}`}>
              DISASTERSHIELD AI
            </div>
            <div className="text-[9px] font-mono uppercase tracking-widest text-cyan-500/70">
              Tactical Decision Node
            </div>
          </div>
        </button>

        <nav className="hidden md:flex items-center gap-1">
          {items.map((it) => (
            <button
              key={it.id}
              onClick={() => setView(it.id)}
              className={`px-3 py-1.5 rounded text-xs font-mono uppercase tracking-widest transition-colors ${
                isActive(it.id)
                  ? `${accentText(theme, "cyan")} bg-cyan-400/10 border border-cyan-400/30`
                  : `${s.textSecondary} hover:${s.textPrimary} border border-transparent`
              }`}
            >
              {it.label}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <button
            onClick={toggle}
            aria-label="Toggle theme"
            className={`w-7 h-7 rounded flex items-center justify-center border ${s.borderSoft} ${s.tint} hover:${s.tintStrong}`}
          >
            {theme === "dark" ? (
              <Sun className="w-3.5 h-3.5 text-amber-400" />
            ) : (
              <Moon className="w-3.5 h-3.5 text-slate-600" />
            )}
          </button>
          <Badge className="bg-emerald-400/10 text-emerald-500 border border-emerald-400/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />{" "}
            System Online
          </Badge>
          <span className={s.textSecondary}>
            <Clock24 />
          </span>
        </div>
      </div>
    </div>
  );
}
