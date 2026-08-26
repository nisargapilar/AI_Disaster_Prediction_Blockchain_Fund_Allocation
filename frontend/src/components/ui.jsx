import { useState, useEffect } from "react";
import {
  useTheme,
  surface,
  accentText,
  sevColors,
} from "../theme/ThemeContext";

export function Badge({ children, className = "" }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-widest ${className}`}
    >
      {children}
    </span>
  );
}

export function SevBadge({ severity }) {
  const { theme } = useTheme();
  const c = sevColors(theme)[severity] ?? sevColors(theme).low;
  return (
    <Badge className={`${c.bg} ${c.text} border ${c.border}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {severity.replace("_", " ")} severity
    </Badge>
  );
}

export function Panel({
  title,
  icon: Icon,
  accent = "cyan",
  right,
  children,
  dashed = false,
}) {
  const { theme } = useTheme();
  const s = surface(theme);
  const accentTextCls =
    accent === "violet"
      ? accentText(theme, "violet")
      : accentText(theme, "cyan");
  const accentBorder =
    accent === "violet" ? "border-violet-400/30" : "border-cyan-400/20";
  return (
    <div
      className={`rounded-md ${s.panel} border ${dashed ? "border-dashed" : ""} ${accentBorder} overflow-hidden`}
    >
      <div
        className={`flex items-center justify-between px-4 py-2.5 border-b ${accentBorder} ${s.tint}`}
      >
        <div
          className={`flex items-center gap-2 text-xs font-mono uppercase tracking-widest ${accentTextCls}`}
        >
          {Icon && <Icon className="w-3.5 h-3.5" />}
          {title}
        </div>
        {right}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

export function Clock24() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <span className="font-mono text-[11px] opacity-70">
      {now.toISOString().slice(0, 19).replace("T", " ")} UTC
    </span>
  );
}
