"""
backend/modules/notify/email_templates.py

HTML email templates matching the DisasterShield AI dashboard styling.
Kept deliberately simple (inline styles, no flexbox/grid) since most email
clients strip or ignore modern CSS — this is the "email-safe" version of
the same dark/cyan look used in the frontend and the status pages.
"""

def _shell(inner_html: str, preheader: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>DisasterShield AI</title>
</head>
<body style="margin:0; padding:0; background-color:#05070b; font-family: 'Courier New', Courier, monospace;">
  <div style="display:none; max-height:0; overflow:hidden;">{preheader}</div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#05070b; padding: 32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="max-width:480px; width:100%; background-color:#0a0f16; border:1px solid rgba(34,211,238,0.25); border-radius:8px; overflow:hidden;">

          <!-- header -->
          <tr>
            <td style="padding:20px 28px; border-bottom:1px solid rgba(34,211,238,0.15); background-color:#070b10;">
              <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="width:32px; height:32px; background-color:rgba(34,211,238,0.1); border:1px solid rgba(34,211,238,0.4); border-radius:6px; text-align:center; vertical-align:middle; font-size:16px; color:#22d3ee;">◆</td>
                  <td style="padding-left:10px;">
                    <div style="font-size:13px; font-weight:bold; color:#f1f5f9; letter-spacing:0.03em;">DISASTERSHIELD AI</div>
                    <div style="font-size:9px; color:#64748b; letter-spacing:0.15em; text-transform:uppercase;">Tactical Decision Node</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- body -->
          <tr>
            <td style="padding:28px;">
              {inner_html}
            </td>
          </tr>

          <!-- footer -->
          <tr>
            <td style="padding:16px 28px; border-top:1px solid rgba(255,255,255,0.06); background-color:#070b10;">
              <div style="font-size:10px; color:#475569; line-height:1.6;">
                You're receiving this because you subscribed to disaster alerts.
                This is an automated message from a monitoring system — not a confirmed emergency notification unless stated otherwise.
              </div>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _button(label: str, url: str, color: str = "#22d3ee", border: str = "rgba(34,211,238,0.4)", bg: str = "rgba(34,211,238,0.1)") -> str:
    return f"""
    <table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:20px;">
      <tr>
        <td style="background-color:{bg}; border:1px solid {border}; border-radius:6px;">
          <a href="{url}" style="display:inline-block; padding:11px 22px; font-size:11px; font-weight:bold; letter-spacing:0.08em; text-transform:uppercase; color:{color}; text-decoration:none; font-family: 'Courier New', Courier, monospace;">
            {label}
          </a>
        </td>
      </tr>
    </table>
    """


def _token_box(token: str) -> str:
    return f"""
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-top:16px;">
      <tr>
        <td style="padding:14px 16px; background-color:rgba(255,255,255,0.03); border:1px dashed rgba(34,211,238,0.35); border-radius:6px; text-align:center;">
          <div style="font-size:9px; color:#64748b; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:8px;">
            Or paste this token manually
          </div>
          <div style="font-size:15px; font-weight:bold; color:#22d3ee; letter-spacing:0.05em; word-break:break-all; user-select:all;">
            {token}
          </div>
        </td>
      </tr>
    </table>
    """


def confirmation_email(confirm_url: str, confirm_token: str) -> str:
    body = f"""
      <div style="display:inline-block; padding:3px 10px; background-color:rgba(34,211,238,0.1); border:1px solid rgba(34,211,238,0.3); border-radius:4px; font-size:9px; color:#22d3ee; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:16px;">
        Action Required
      </div>
      <h1 style="margin:0 0 10px; font-size:17px; color:#f1f5f9; font-weight:bold;">Confirm your subscription</h1>
      <p style="margin:0 0 4px; font-size:13px; line-height:1.7; color:#94a3b8;">
        One click and you're set to receive early-warning alerts when prediction risk crosses the threshold for your selected region and disaster type.
      </p>
      {_button("Confirm Subscription", confirm_url)}
      {_token_box(confirm_token)}
      <p style="margin:24px 0 0; font-size:11px; line-height:1.6; color:#475569;">
        If you didn't request this, you can safely ignore this email — no subscription will be created.
      </p>
    """
    return _shell(body, preheader="Confirm your disaster alert subscription")


def prediction_alert_email(disaster_type: str, region: str, risk_score: float, severity_tier: str, unsub_url: str) -> str:
    sev = severity_tier.lower()
    accent = {"low": "#34d399", "medium": "#fbbf24", "high": "#fb923c", "critical": "#fb7185"}.get(sev, "#a78bfa")
    body = f"""
      <div style="display:inline-block; padding:3px 10px; background-color:rgba(167,139,250,0.1); border:1px dashed rgba(167,139,250,0.4); border-radius:4px; font-size:9px; color:#a78bfa; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:16px;">
        Risk Indicator — Not a Confirmed Event
      </div>
      <h1 style="margin:0 0 10px; font-size:17px; color:#f1f5f9; font-weight:bold;">
        {disaster_type.title()} risk in {region}
      </h1>
      <table role="presentation" cellpadding="0" cellspacing="0" style="margin:14px 0;">
        <tr>
          <td style="padding-right:20px;">
            <div style="font-size:9px; color:#64748b; letter-spacing:0.1em; text-transform:uppercase;">Severity</div>
            <div style="font-size:14px; color:{accent}; font-weight:bold; text-transform:uppercase;">{sev}</div>
          </td>
          <td>
            <div style="font-size:9px; color:#64748b; letter-spacing:0.1em; text-transform:uppercase;">Risk Score</div>
            <div style="font-size:14px; color:{accent}; font-weight:bold;">{risk_score:.2f}</div>
          </td>
        </tr>
      </table>
      <p style="margin:0; font-size:12px; line-height:1.7; color:#94a3b8;">
        This is an automated early-warning signal from the prediction module — it has not touched fund status and does not indicate a confirmed disaster.
      </p>
      {_button("Manage Subscription", unsub_url, color="#94a3b8", border="rgba(255,255,255,0.12)", bg="rgba(255,255,255,0.03)")}
    """
    return _shell(body, preheader=f"{sev.title()} {disaster_type} risk detected in {region}")


def digest_email(summary_lines: list[str], unsub_url: str) -> str:
    if summary_lines and summary_lines[0].startswith("No new predictions"):
        rows = f'<p style="font-size:12px; color:#64748b;">{summary_lines[0]}</p>'
    else:
        row_html = []
        for line in summary_lines:
            row_html.append(f"""
              <tr>
                <td style="padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.05); font-size:11px; color:#cbd5e1; font-family:'Courier New',monospace;">
                  {line}
                </td>
              </tr>
            """)
        rows = f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{"".join(row_html)}</table>'

    body = f"""
      <div style="display:inline-block; padding:3px 10px; background-color:rgba(34,211,238,0.1); border:1px solid rgba(34,211,238,0.3); border-radius:4px; font-size:9px; color:#22d3ee; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:16px;">
        Daily Digest
      </div>
      <h1 style="margin:0 0 14px; font-size:17px; color:#f1f5f9; font-weight:bold;">Your 24-hour monitoring summary</h1>
      {rows}
      {_button("Manage Subscription", unsub_url, color="#94a3b8", border="rgba(255,255,255,0.12)", bg="rgba(255,255,255,0.03)")}
    """
    return _shell(body, preheader="Your daily disaster monitoring digest")