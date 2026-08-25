import { createContext, useContext, useState } from "react";

// Dark is the primary design; light is a secondary reading mode.
// The tactical map panel always stays dark (radar-screen convention) in
// both themes — only surrounding chrome switches. See TacticalMap.jsx.
const ThemeContext = createContext({ theme: "dark", toggle: () => {} });

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState("dark");
  const toggle = () => setTheme((t) => (t === "dark" ? "light" : "dark"));
  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);

export function surface(theme) {
  return theme === "dark"
    ? {
        app: "bg-[#05070b]",
        panel: "bg-[#0a0f16]",
        nav: "bg-[#070b10]",
        borderFaint: "border-white/5",
        borderSoft: "border-white/10",
        tint: "bg-white/[0.02]",
        tintStrong: "bg-white/[0.03]",
        divideFaint: "divide-white/5",
        textPrimary: "text-slate-100",
        textBody: "text-slate-200",
        textSecondary: "text-slate-400",
        textMuted: "text-slate-500",
        textFaint: "text-slate-600",
      }
    : {
        app: "bg-[#eef1f5]",
        panel: "bg-white",
        nav: "bg-[#e4e9ef]",
        borderFaint: "border-slate-900/[0.06]",
        borderSoft: "border-slate-900/[0.12]",
        tint: "bg-slate-900/[0.02]",
        tintStrong: "bg-slate-900/[0.04]",
        divideFaint: "divide-slate-900/[0.06]",
        textPrimary: "text-slate-900",
        textBody: "text-slate-800",
        textSecondary: "text-slate-600",
        textMuted: "text-slate-500",
        textFaint: "text-slate-400",
      };
}

// Accent TEXT darkens in light mode for contrast; accent bg/border tints stay
// fixed across both themes since a translucent tint reads fine on white too.
export function accentText(theme, name) {
  const map = {
    cyan: { dark: "text-cyan-300", light: "text-cyan-700" },
    cyanAlt: { dark: "text-cyan-400", light: "text-cyan-600" },
    violet: { dark: "text-violet-300", light: "text-violet-700" },
    violetAlt: { dark: "text-violet-400", light: "text-violet-600" },
    emerald: { dark: "text-emerald-400", light: "text-emerald-700" },
    amber: { dark: "text-amber-400", light: "text-amber-700" },
    orange: { dark: "text-orange-300", light: "text-orange-700" },
    rose: { dark: "text-rose-400", light: "text-rose-700" },
  };
  return map[name]?.[theme] ?? "";
}

export function sevColors(theme) {
  return {
    low: {
      text: accentText(theme, "emerald"),
      bg: "bg-emerald-400/10",
      border: "border-emerald-400/40",
      dot: "bg-emerald-400",
    },
    medium: {
      text: accentText(theme, "amber"),
      bg: "bg-amber-400/10",
      border: "border-amber-400/40",
      dot: "bg-amber-400",
    },
    high: {
      text: accentText(theme, "orange"),
      bg: "bg-orange-400/10",
      border: "border-orange-400/40",
      dot: "bg-orange-400",
    },
    critical: {
      text: accentText(theme, "rose"),
      bg: "bg-rose-400/10",
      border: "border-rose-400/40",
      dot: "bg-rose-400",
    },
  };
}
