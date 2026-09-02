import { useState } from "react";
import {
  Bell,
  Mail,
  Send,
  KeyRound,
  Loader2,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { useTheme, surface, accentText } from "../theme/ThemeContext";
import { Badge, Panel } from "../components/ui";
import {
  subscribe,
  confirmSubscription,
  requestUnsubscribeLink,
  unsubscribe,
  digestNow,
} from "../api/subscribe";

const DISASTER_OPTIONS = [
  { value: "all", label: "All disaster types" },
  { value: "earthquake", label: "Earthquake" },
  { value: "cyclone", label: "Cyclone" },
  { value: "flood", label: "Flood" },
  { value: "forest_fire", label: "Forest Fire" },
];

function fieldCls(s) {
  return `w-full rounded px-3 py-2 text-sm bg-transparent border ${s.borderSoft} ${s.textBody} placeholder:${s.textFaint} focus:outline-none focus:border-violet-400/50`;
}

export default function Subscribe() {
  const { theme } = useTheme();
  const s = surface(theme);

  // subscribe form
  const [email, setEmail] = useState("");
  const [region, setRegion] = useState("");
  const [disasterType, setDisasterType] = useState("all");
  const [subStatus, setSubStatus] = useState("idle"); // idle | loading | done | error
  const [subError, setSubError] = useState("");

  // confirm-by-token
  const [confirmToken, setConfirmToken] = useState("");
  const [confirmStatus, setConfirmStatus] = useState("idle");
  const [confirmResult, setConfirmResult] = useState("");

  // unsubscribe — request a link by email (mirrors "subscribe")
  const [unsubEmail, setUnsubEmail] = useState("");
  const [unsubEmailStatus, setUnsubEmailStatus] = useState("idle"); // idle | loading | done | error

  // unsubscribe — confirm with token (mirrors "confirm subscription")
  const [unsubToken, setUnsubToken] = useState("");
  const [unsubTokenStatus, setUnsubTokenStatus] = useState("idle");
  const [unsubTokenResult, setUnsubTokenResult] = useState("");

  // admin digest
  const [digestStatus, setDigestStatus] = useState("idle");

  const handleSubscribe = async (e) => {
    e.preventDefault();
    setSubStatus("loading");
    setSubError("");
    try {
      await subscribe({
        email,
        region: region || "",
        disaster_type: disasterType === "all" ? "" : disasterType,
      });
      setSubStatus("done");
    } catch (err) {
      setSubStatus("error");
      setSubError(err.message);
    }
  };

  const handleConfirm = async () => {
    if (!confirmToken) return;
    setConfirmStatus("loading");
    try {
      const res = await confirmSubscription(confirmToken);
      setConfirmResult(res.status);
      setConfirmStatus("done");
    } catch (err) {
      setConfirmResult(err.message);
      setConfirmStatus("error");
    }
  };

  const handleUnsubRequest = async (e) => {
    e.preventDefault();
    setUnsubEmailStatus("loading");
    try {
      await requestUnsubscribeLink(unsubEmail);
      setUnsubEmailStatus("done");
    } catch {
      setUnsubEmailStatus("error");
    }
  };

  const handleUnsubByToken = async () => {
    if (!unsubToken) return;
    setUnsubTokenStatus("loading");
    try {
      const res = await unsubscribe(unsubToken);
      setUnsubTokenResult(res.status);
      setUnsubTokenStatus("done");
    } catch (err) {
      setUnsubTokenResult(err.message);
      setUnsubTokenStatus("error");
    }
  };

  const runDigestNow = async () => {
    setDigestStatus("loading");
    try {
      await digestNow();
      setDigestStatus("done");
    } catch {
      setDigestStatus("error");
    }
  };

  return (
    <div className="p-5 max-w-3xl mx-auto space-y-4">
      <div>
        <div
          className={`text-xs font-mono uppercase tracking-widest mb-1 ${accentText(theme, "violet")}`}
        >
          Alerts // Email Subscription
        </div>
        <div className={`text-sm ${s.textSecondary}`}>
          Get an email when prediction risk crosses the alert threshold for a
          region or disaster type. Subscribing never grants access to fund data
          — it's a read-only warning channel.
        </div>
      </div>

      <Panel title="Subscribe" icon={Mail} accent="violet">
        <form onSubmit={handleSubscribe} className="space-y-3">
          <div>
            <label
              className={`block text-[10px] font-mono uppercase mb-1 ${s.textMuted}`}
            >
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className={fieldCls(s)}
            />
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <label
                className={`block text-[10px] font-mono uppercase mb-1 ${s.textMuted}`}
              >
                Region (optional)
              </label>
              <input
                type="text"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                placeholder="e.g. Sulawesi, CA, Alaska"
                className={fieldCls(s)}
              />
            </div>
            <div>
              <label
                className={`block text-[10px] font-mono uppercase mb-1 ${s.textMuted}`}
              >
                Disaster type
              </label>
              <select
                value={disasterType}
                onChange={(e) => setDisasterType(e.target.value)}
                className={fieldCls(s)}
              >
                {DISASTER_OPTIONS.map((o) => (
                  <option
                    key={o.value}
                    value={o.value}
                    className="bg-[#0a0f16]"
                  >
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={subStatus === "loading"}
            className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-mono uppercase tracking-widest border border-violet-400/40 bg-violet-400/10 ${accentText(theme, "violet")} hover:bg-violet-400/20 transition-colors disabled:opacity-50`}
          >
            {subStatus === "loading" ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
            Subscribe
          </button>

          {subStatus === "done" && (
            <div className="flex items-center gap-2 text-xs text-emerald-500">
              <CheckCircle2 className="w-3.5 h-3.5" /> Check your inbox to
              confirm your subscription.
            </div>
          )}
          {subStatus === "error" && (
            <div className="flex items-center gap-2 text-xs text-rose-500">
              <AlertTriangle className="w-3.5 h-3.5" /> {subError}
            </div>
          )}
        </form>
      </Panel>

      <Panel
        title="Confirm Subscription"
        icon={KeyRound}
        accent="violet"
        right={
          <Badge className={`${s.tint} ${s.textFaint} border ${s.borderSoft}`}>
            From email
          </Badge>
        }
      >
        <div className={`text-xs mb-3 ${s.textSecondary}`}>
          Paste the token from your confirmation email (the part after{" "}
          <code>/subscribe/confirm/</code> in the link).
        </div>
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            value={confirmToken}
            onChange={(e) => setConfirmToken(e.target.value)}
            placeholder="paste confirm token here"
            className={`${fieldCls(s)} sm:flex-1`}
          />
          <button
            onClick={handleConfirm}
            disabled={!confirmToken || confirmStatus === "loading"}
            className="px-3 py-2 rounded text-xs font-mono uppercase tracking-widest border border-emerald-400/30 bg-emerald-400/10 text-emerald-600 hover:bg-emerald-400/20 disabled:opacity-40 flex items-center gap-1.5 justify-center"
          >
            {confirmStatus === "loading" ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              "Confirm"
            )}
          </button>
        </div>
        {confirmStatus === "done" && (
          <div className="flex items-center gap-2 text-xs text-emerald-500 mt-2">
            <CheckCircle2 className="w-3.5 h-3.5" /> {confirmResult}
          </div>
        )}
        {confirmStatus === "error" && (
          <div className="flex items-center gap-2 text-xs text-rose-500 mt-2">
            <AlertTriangle className="w-3.5 h-3.5" /> {confirmResult}
          </div>
        )}
      </Panel>

      <Panel title="Unsubscribe" icon={Mail} accent="violet">
        <form onSubmit={handleUnsubRequest} className="space-y-3">
          <div>
            <label
              className={`block text-[10px] font-mono uppercase mb-1 ${s.textMuted}`}
            >
              Email
            </label>
            <input
              type="email"
              required
              value={unsubEmail}
              onChange={(e) => setUnsubEmail(e.target.value)}
              placeholder="the email you subscribed with"
              className={fieldCls(s)}
            />
          </div>

          <button
            type="submit"
            disabled={unsubEmailStatus === "loading"}
            className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-mono uppercase tracking-widest border border-violet-400/40 bg-violet-400/10 ${accentText(theme, "violet")} hover:bg-violet-400/20 transition-colors disabled:opacity-50`}
          >
            {unsubEmailStatus === "loading" ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
            Unsubscribe
          </button>

          {unsubEmailStatus === "done" && (
            <div className="flex items-center gap-2 text-xs text-emerald-500">
              <CheckCircle2 className="w-3.5 h-3.5" /> Check your inbox to
              confirm unsubscribing.
            </div>
          )}
          {unsubEmailStatus === "error" && (
            <div className="flex items-center gap-2 text-xs text-rose-500">
              <AlertTriangle className="w-3.5 h-3.5" /> Something went wrong.
              Please try again.
            </div>
          )}
        </form>
      </Panel>

      <Panel
        title="Confirm Unsubscribe"
        icon={KeyRound}
        accent="violet"
        right={
          <Badge className={`${s.tint} ${s.textFaint} border ${s.borderSoft}`}>
            From email
          </Badge>
        }
      >
        <div className={`text-xs mb-3 ${s.textSecondary}`}>
          Paste the token from your unsubscribe email (the part after{" "}
          <code>/subscribe/unsubscribe/confirm/</code> in the link).
        </div>
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            value={unsubToken}
            onChange={(e) => setUnsubToken(e.target.value)}
            placeholder="paste unsubscribe token here"
            className={`${fieldCls(s)} sm:flex-1`}
          />
          <button
            onClick={handleUnsubByToken}
            disabled={!unsubToken || unsubTokenStatus === "loading"}
            className="px-3 py-2 rounded text-xs font-mono uppercase tracking-widest border border-emerald-400/30 bg-emerald-400/10 text-emerald-600 hover:bg-emerald-400/20 disabled:opacity-40 flex items-center gap-1.5 justify-center"
          >
            {unsubTokenStatus === "loading" ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              "Confirm"
            )}
          </button>
        </div>
        {unsubTokenStatus === "done" && (
          <div className="flex items-center gap-2 text-xs text-emerald-500 mt-2">
            <CheckCircle2 className="w-3.5 h-3.5" /> {unsubTokenResult}
          </div>
        )}
        {unsubTokenStatus === "error" && (
          <div className="flex items-center gap-2 text-xs text-rose-500 mt-2">
            <AlertTriangle className="w-3.5 h-3.5" /> {unsubTokenResult}
          </div>
        )}
      </Panel>

      <Panel
        title="Digest Control"
        icon={Bell}
        accent="cyan"
        right={
          <Badge className="bg-cyan-400/10 text-cyan-600 border border-cyan-400/30">
            Admin only
          </Badge>
        }
      >
        <div className={`text-xs mb-3 ${s.textSecondary}`}>
          Digests normally send on a schedule. Trigger one immediately for a
          demo.
        </div>
        <button
          onClick={runDigestNow}
          disabled={digestStatus === "loading"}
          className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-mono uppercase tracking-widest border border-cyan-400/40 bg-cyan-400/10 ${accentText(theme, "cyan")} hover:bg-cyan-400/20 disabled:opacity-50`}
        >
          {digestStatus === "loading" ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Send className="w-3.5 h-3.5" />
          )}
          Send Digest Now
        </button>
        {digestStatus === "done" && (
          <div className="text-xs text-emerald-500 mt-2">
            Digest job triggered.
          </div>
        )}
        {digestStatus === "error" && (
          <div className="text-xs text-rose-500 mt-2">
            Digest trigger failed.
          </div>
        )}
      </Panel>
    </div>
  );
}
