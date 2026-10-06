import { useState, useEffect } from "react";
import { ListChecks, RefreshCw } from "lucide-react";
import { useTheme, surface, accentText } from "../../theme/ThemeContext";
import { Panel, Badge, SevBadge } from "../../components/ui";
import Breadcrumb from "../../components/Breadcrumb";
import { fetchDashboard } from "../../api/blockchain";

const STATUS_STYLES = {
  verified: "bg-emerald-500/10 text-emerald-400 border-emerald-400/30",
  already_verified: "bg-sky-500/10 text-sky-400 border-sky-400/30",
  pending: "bg-amber-500/10 text-amber-400 border-amber-400/30",
  failed: "bg-red-500/10 text-red-400 border-red-400/30",
};

function RecordStatusBadge({ status }) {
  const cls = STATUS_STYLES[status] || STATUS_STYLES.pending;
  return <Badge className={`border ${cls}`}>{status}</Badge>;
}

export default function VerifiedBeneficiaries() {
  const { theme } = useTheme();
  const s = surface(theme);

  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDashboard();
      // raw events — kept un-normalized so distribution_records survives
      setEvents(data.events || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    queueMicrotask(() => {
      load();
    });
  }, []);

  const eventsWithRecords = events.filter(
    (ev) => (ev.distribution_records || []).length > 0,
  );

  return (
    <div>
      <Breadcrumb trail={["Dashboard", "Funds", "Verified"]} />
      <div className="p-5 max-w-5xl mx-auto space-y-5">
        <Panel
          title="Verified Beneficiaries"
          icon={ListChecks}
          accent="emerald"
          right={
            <button
              onClick={load}
              className={`flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest ${accentText(theme, "emerald")} opacity-70 hover:opacity-100`}
            >
              <RefreshCw className="w-3 h-3" />
              refresh
            </button>
          }
        >
          {loading && (
            <p className={`text-sm font-mono ${s.textSecondary}`}>loading...</p>
          )}
          {error && (
            <p className="text-sm font-mono text-red-400">error: {error}</p>
          )}
          {!loading && !error && eventsWithRecords.length === 0 && (
            <p className={`text-sm font-mono ${s.textSecondary}`}>
              no beneficiaries verified yet
            </p>
          )}

          {!loading && eventsWithRecords.length > 0 && (
            <div className="space-y-4">
              {eventsWithRecords.map((ev) => (
                <div
                  key={ev.event_id}
                  className={`rounded border border-white/10 ${s.panel}`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 border-b border-white/5">
                    <div className="flex flex-col">
                      <span className={`text-sm font-mono ${s.textPrimary}`}>
                        {ev.disaster_type} — {ev.region}
                      </span>
                      <span
                        className={`text-[10px] font-mono ${s.textSecondary}`}
                      >
                        {new Date(ev.event_time).toLocaleString()}
                      </span>
                    </div>
                    <SevBadge severity={ev.severity_tier} />
                  </div>

                  <div className="divide-y divide-white/5">
                    {ev.distribution_records.map((rec) => (
                      <div
                        key={rec.record_id}
                        className="flex flex-wrap items-center justify-between gap-2 px-3 py-2"
                      >
                        <div className="flex flex-col">
                          <span
                            className={`text-xs font-mono ${s.textPrimary}`}
                          >
                            {rec.mock_name || "Unnamed"} — ID ending in{" "}
                            {rec.mock_id_last4 || "----"}
                          </span>
                          {rec.tx_hash && (
                            <a
                              href={`https://amoy.polygonscan.com/tx/${rec.tx_hash}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={`text-[10px] font-mono truncate max-w-xs underline hover:opacity-80 ${s.textSecondary}`}
                            >
                              tx: {rec.tx_hash}
                            </a>
                          )}
                        </div>
                        <RecordStatusBadge status={rec.status} />
                      </div>
                    ))}
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
