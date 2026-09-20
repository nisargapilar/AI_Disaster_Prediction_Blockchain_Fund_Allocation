import { useState, useEffect } from "react";
import { Landmark, ShieldCheck, RefreshCw } from "lucide-react";
import { useTheme, surface, accentText } from "../../theme/ThemeContext";
import { Panel, Badge, SevBadge } from "../../components/ui";
import Breadcrumb from "../../components/Breadcrumb";
import {
  fetchDashboard,
  verifyBeneficiary,
  normalizeFundEvent,
} from "../../api/blockchain";

const STATUS_STYLES = {
  released: "bg-emerald-500/10 text-emerald-400 border-emerald-400/30",
  pending: "bg-amber-500/10 text-amber-400 border-amber-400/30",
  failed: "bg-red-500/10 text-red-400 border-red-400/30",
};

function FundStatusBadge({ status }) {
  const cls = STATUS_STYLES[status] || STATUS_STYLES.pending;
  return <Badge className={`border ${cls}`}>{status}</Badge>;
}

export default function FundsPlaceholder() {
  const { theme } = useTheme();
  const s = surface(theme);

  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedEventId, setSelectedEventId] = useState("");
  const [mockId, setMockId] = useState("");
  const [verifyResult, setVerifyResult] = useState(null);
  const [verifying, setVerifying] = useState(false);

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

  async function handleVerify(e) {
    e.preventDefault();
    if (!selectedEventId || mockId.length < 4) return;
    setVerifying(true);
    setVerifyResult(null);
    try {
      const result = await verifyBeneficiary(selectedEventId, mockId);
      setVerifyResult({ ok: true, ...result });
      setMockId("");
      loadDashboard();
    } catch (err) {
      setVerifyResult({ ok: false, error: err.message });
    } finally {
      setVerifying(false);
    }
  }

  return (
    <div>
      <Breadcrumb trail={["Dashboard", "Funds"]} />
      <div className="p-5 max-w-5xl mx-auto space-y-5">
        {/* Fund release ledger */}
        <Panel
          title="Blockchain / Fund Ledger"
          icon={Landmark}
          accent="cyan"
          right={
            <button
              onClick={loadDashboard}
              className={`flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest ${accentText(theme, "cyan")} opacity-70 hover:opacity-100`}
            >
              <RefreshCw className="w-3 h-3" />
              refresh
            </button>
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

        {/* Beneficiary verification form */}
        <Panel title="Verify Beneficiary" icon={ShieldCheck} accent="violet">
          <form onSubmit={handleVerify} className="space-y-3">
            <div>
              <label
                className={`block text-[10px] font-mono uppercase tracking-widest mb-1 ${s.textSecondary}`}
              >
                Event
              </label>
              <select
                value={selectedEventId}
                onChange={(e) => setSelectedEventId(e.target.value)}
                className={`w-full px-3 py-2 rounded border border-white/10 bg-transparent text-sm font-mono ${s.textPrimary}`}
              >
                <option value="">select an event...</option>
                {events
                  .filter((ev) => ev.fundStatus === "released")
                  .map((ev) => (
                    <option key={ev.id} value={ev.id}>
                      {ev.disasterType} — {ev.region} ({ev.eventTime})
                    </option>
                  ))}
              </select>
            </div>

            <div>
              <label
                className={`block text-[10px] font-mono uppercase tracking-widest mb-1 ${s.textSecondary}`}
              >
                Mock Beneficiary ID
              </label>
              <input
                type="text"
                value={mockId}
                onChange={(e) => setMockId(e.target.value)}
                placeholder="e.g. 123456789012"
                className={`w-full px-3 py-2 rounded border border-white/10 bg-transparent text-sm font-mono ${s.textPrimary}`}
              />
            </div>

            <button
              type="submit"
              disabled={verifying || !selectedEventId || mockId.length < 4}
              className={`px-4 py-2 rounded text-xs font-mono uppercase tracking-widest border ${accentText(theme, "violet")} border-violet-400/30 hover:bg-violet-400/10 disabled:opacity-40`}
            >
              {verifying ? "verifying..." : "verify on-chain"}
            </button>
          </form>

          {verifyResult && (
            <div
              className={`mt-3 px-3 py-2 rounded border text-xs font-mono ${
                verifyResult.ok
                  ? "border-emerald-400/30 text-emerald-400"
                  : "border-red-400/30 text-red-400"
              }`}
            >
              {verifyResult.ok ? (
                <>
                  status: {verifyResult.status}
                  {verifyResult.tx_hash && (
                    <div className="truncate">tx: {verifyResult.tx_hash}</div>
                  )}
                </>
              ) : (
                <>error: {verifyResult.error}</>
              )}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
