import { ChevronRight } from "lucide-react";
import { useTheme, surface, accentText } from "../theme/ThemeContext";

export default function Breadcrumb({ trail }) {
  const { theme } = useTheme();
  const s = surface(theme);
  return (
    <div
      className={`px-5 py-2 border-b border-dashed border-cyan-400/15 ${s.nav} flex items-center gap-1.5 text-[11px] font-mono ${s.textMuted}`}
    >
      {trail.map((t, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <ChevronRight className="w-3 h-3" />}
          <span
            className={i === trail.length - 1 ? accentText(theme, "cyan") : ""}
          >
            {t}
          </span>
        </span>
      ))}
    </div>
  );
}
