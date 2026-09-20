import { useState, useEffect, useRef } from "react";
import { ShieldCheck, ScanLine } from "lucide-react";
import { Html5QrcodeScanner } from "html5-qrcode";
import { useTheme, surface, accentText } from "../../theme/ThemeContext";
import { Panel } from "../../components/ui";
import Breadcrumb from "../../components/Breadcrumb";
import {
  fetchDashboard,
  verifyBeneficiary,
  normalizeFundEvent,
} from "../../api/blockchain";

export default function VerifyBeneficiary() {
  const { theme } = useTheme();
  const s = surface(theme);

  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState("");
  const [mockId, setMockId] = useState("");
  const [verifyResult, setVerifyResult] = useState(null);
  const [verifying, setVerifying] = useState(false);

  const [showScanner, setShowScanner] = useState(false);
  const scannerRef = useRef(null);

  useEffect(() => {
    async function loadEvents() {
      try {
        const data = await fetchDashboard();
        setEvents(data.events.map(normalizeFundEvent));
      } catch {
        // event list is best-effort here; verify form just shows empty options on failure
      }
    }
    loadEvents();
  }, []);

  useEffect(() => {
    if (!showScanner) return;

    const scanner = new Html5QrcodeScanner(
      "qr-scanner-box",
      { fps: 10, qrbox: 220 },
      false,
    );
    scannerRef.current = scanner;

    scanner.render(
      (decodedText) => {
        let scannedId = decodedText;
        try {
          const parsed = JSON.parse(decodedText);
          if (parsed.id) scannedId = parsed.id;
        } catch {
          // not JSON — treat decodedText as the raw ID
        }
        setMockId(scannedId);
        setShowScanner(false);
      },
      () => {},
    );

    return () => {
      scanner.clear().catch(() => {});
    };
  }, [showScanner]);

  async function handleVerify(e) {
    e.preventDefault();
    if (!selectedEventId || mockId.length < 4) return;
    setVerifying(true);
    setVerifyResult(null);
    try {
      const result = await verifyBeneficiary(selectedEventId, mockId);
      setVerifyResult({ ok: true, ...result });
      setMockId("");
    } catch (err) {
      setVerifyResult({ ok: false, error: err.message });
    } finally {
      setVerifying(false);
    }
  }

  return (
    <div>
      <Breadcrumb trail={["Dashboard", "Funds", "Verify"]} />
      <div className="p-5 max-w-2xl mx-auto space-y-5">
        <Panel title="Verify Beneficiary" icon={ShieldCheck} accent="violet">
          <button
            type="button"
            onClick={() => setShowScanner((v) => !v)}
            className={`mb-3 flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest ${accentText(theme, "violet")} opacity-70 hover:opacity-100`}
          >
            <ScanLine className="w-3 h-3" />
            {showScanner ? "close scanner" : "scan beneficiary card"}
          </button>

          {showScanner && <div id="qr-scanner-box" className="mb-3" />}

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
