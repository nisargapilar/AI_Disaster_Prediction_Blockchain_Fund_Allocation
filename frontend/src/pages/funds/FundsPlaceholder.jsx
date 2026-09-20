import { useState, useEffect } from "react";
import { Landmark, RefreshCw } from "lucide-react";
import { useTheme, surface, accentText } from "../../theme/ThemeContext";
import { Panel, Badge, SevBadge } from "../../components/ui";
import Breadcrumb from "../../components/Breadcrumb";
import { fetchDashboard, normalizeFundEvent } from "../../api/blockchain";

const STATUS_STYLES = {
  released: "bg-emerald-500/10 text-emerald-400 border-emerald-400/30",
  pending: "bg-amber-500/10 text-amber-400 border-amber-400/30",
  failed: "bg-red-500/10 text-red-400 border-red-400/30",
};

function FundStatusBadge({ status }) {
  const cls = STATUS_STYLES[status] || STATUS_STYLES.pending;
  return <Badge className={`border ${cls}`}>{status}</Badge>;
}

export default function FundsPlaceholder({ setView }) {
  const { theme } = useTheme();
  const s = surface(theme);

  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function loadDashboard() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDashboard();
      setEvents(data.events.map(normalizeFundEvent));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    queueMicrotask(() => {
      loadDashboard();
    });
  }, []);

  return (
    <div>
      <Breadcrumb trail={["Dashboard", "Funds"]} />
      <div className="p-5 max-w-5xl mx-auto space-y-5">
        <Panel
          title="Blockchain / Fund Ledger"
          icon={Landmark}
          accent="cyan"
          right={
            <div className="flex items-center gap-3">
              {setView && (
                <button
                  onClick={() => setView("verify-beneficiary")}
                  className={`text-[10px] font-mono uppercase tracking-widest ${accentText(theme, "violet")} opacity-70 hover:opacity-100`}
                >
                  verify beneficiary →
                </button>
              )}
              <button
                onClick={loadDashboard}
                className={`flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest ${accentText(theme, "cyan")} opacity-70 hover:opacity-100`}
              >
                <RefreshCw className="w-3 h-3" />
                refresh
              </button>
            </div>
          }
        >
          {loading && (
            <p className={`text-sm font-mono ${s.textSecondary}`}>
              loading events...
            </p>
          )}
          {error && (
            <p className="text-sm font-mono text-red-400">error: {error}</p>
          )}
          {!loading && !error && events.length === 0 && (
            <p className={`text-sm font-mono ${s.textSecondary}`}>
              no fund-eligible events yet
            </p>
          )}
          {!loading && events.length > 0 && (
            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              {events.map((ev) => (
                <div
                  key={ev.id}
                  className={`flex flex-wrap items-center justify-between gap-2 px-3 py-2 rounded border ${s.panel} border-white/5`}
                >
                  <div className="flex flex-col">
                    <span className="text-sm font-mono">
                      {ev.disasterType} — {ev.region}
                    </span>
                    <span
                      className={`text-[10px] font-mono ${s.textSecondary}`}
                    >
                      {ev.eventTime} · {ev.beneficiariesVerified}{" "}
                      beneficiary(ies) verified
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <SevBadge severity={ev.severity} />
                    <FundStatusBadge status={ev.fundStatus} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
