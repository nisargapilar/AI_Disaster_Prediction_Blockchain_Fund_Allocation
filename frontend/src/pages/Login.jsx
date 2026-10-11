import { useState } from "react";
import { Lock } from "lucide-react";
import { useTheme, surface, accentText } from "../theme/ThemeContext";
import { Panel } from "../components/ui";
import Breadcrumb from "../components/Breadcrumb";
import { useAuth } from "../auth/useAuth";

export default function Login({ setView }) {
  const { theme } = useTheme();
  const s = surface(theme);
  const { login } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(username, password);
      setView("verify-beneficiary");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <Breadcrumb trail={["Dashboard", "Operator Login"]} />
      <div className="p-5 max-w-md mx-auto">
        <Panel title="Operator Login" icon={Lock} accent="violet">
          <p className={`mb-3 text-xs font-mono ${s.textSecondary}`}>
            Only authorized NGO field operators can record beneficiary
            verifications.
          </p>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label
                className={`block text-[10px] font-mono uppercase tracking-widest mb-1 ${s.textSecondary}`}
              >
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                className={`w-full px-3 py-2 rounded border border-white/10 bg-transparent text-sm font-mono ${s.textPrimary}`}
              />
            </div>

            <div>
              <label
                className={`block text-[10px] font-mono uppercase tracking-widest mb-1 ${s.textSecondary}`}
              >
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                className={`w-full px-3 py-2 rounded border border-white/10 bg-transparent text-sm font-mono ${s.textPrimary}`}
              />
            </div>

            <button
              type="submit"
              disabled={submitting || !username || !password}
              className={`px-4 py-2 rounded text-xs font-mono uppercase tracking-widest border ${accentText(theme, "violet")} border-violet-400/30 hover:bg-violet-400/10 disabled:opacity-40`}
            >
              {submitting ? "signing in..." : "sign in"}
            </button>
          </form>

          {error && (
            <div className="mt-3 px-3 py-2 rounded border border-red-400/30 text-xs font-mono text-red-400">
              error: {error}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
