# modules/notify/email_service.py

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from modules.notify.config import BASE_URL
from modules.notify.email_templates import (
    confirmation_email,
    prediction_alert_email,
    digest_email,
    _shell,
    _button,
    _token_box,
)

SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]


def _send(to_email: str, subject: str, text_body: str, html_body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    # Plain text first, HTML second — email clients render the last
    # part they understand, so HTML wins where supported and clients
    # without HTML support fall back to the plain text.
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [to_email], msg.as_string())


async def send_confirmation_email(email: str, token: str):
    link = f"{BASE_URL}/subscribe/confirm/{token}"
    text_body = (
        f"Confirm your subscription to disaster alerts.\n\n"
        f"Click to confirm: {link}\n\n"
        f"Or paste this token manually: {token}\n\n"
        f"If you didn't request this, ignore this email."
    )
    html_body = confirmation_email(link, token)
    _send(email, "Confirm your disaster alert subscription", text_body, html_body)


async def send_unsubscribe_link(email: str, unsubscribe_token: str):
    # Was missing "/confirm/" — this must match the route exactly:
    # GET /subscribe/unsubscribe/confirm/{token} in routes.py
    link = f"{BASE_URL}/subscribe/unsubscribe/confirm/{unsubscribe_token}"
    text_body = (
        f"You requested your unsubscribe link for disaster alerts.\n\n"
        f"Click to unsubscribe: {link}\n\n"
        f"Or paste this token manually: {unsubscribe_token}\n\n"
        f"If you didn't request this, you can safely ignore this email — "
        f"no action will be taken."
    )
    # Same shape as confirmation_email: shell + button + token box, so
    # unsubscribe matches subscribe's confirmation flow exactly.
    html_body = _shell(
        f"""
        <h1 style="margin:0 0 10px; font-size:17px; color:#f1f5f9; font-weight:bold;">Your unsubscribe link</h1>
        <p style="margin:0; font-size:13px; line-height:1.7; color:#94a3b8;">
          You (or someone using this email) requested a link to unsubscribe from disaster alerts.
        </p>
        {_button("Unsubscribe", link, color="#94a3b8", border="rgba(255,255,255,0.12)", bg="rgba(255,255,255,0.03)")}
        {_token_box(unsubscribe_token)}
        <p style="margin:24px 0 0; font-size:11px; line-height:1.6; color:#475569;">
          Didn't request this? No action will be taken — you'll keep receiving alerts as normal.
        </p>
        """,
        preheader="Your disaster alert unsubscribe link",
    )
    _send(email, "Your disaster alert unsubscribe link", text_body, html_body)


async def send_prediction_alert(email: str, unsubscribe_token: str, disaster_type: str,
                                 region: str, risk_score: float, severity_tier: str):
    # Also missing "/confirm/" — same route as above.
    unsub_link = f"{BASE_URL}/subscribe/unsubscribe/confirm/{unsubscribe_token}"
    text_body = (
        f"Early warning: {disaster_type} risk detected in {region}\n"
        f"Severity: {severity_tier.upper()} (risk score: {risk_score:.2f})\n\n"
        f"This is an automated early-warning signal, not a confirmed event.\n\n"
        f"Unsubscribe: {unsub_link}"
    )
    html_body = prediction_alert_email(disaster_type, region, risk_score, severity_tier, unsub_link)
    _send(email, f"[Alert] {severity_tier.upper()} {disaster_type} risk — {region}", text_body, html_body)


async def send_daily_digest(email: str, unsubscribe_token: str, summary_lines: list[str]):
    # Also missing "/confirm/" — same route as above.
    unsub_link = f"{BASE_URL}/subscribe/unsubscribe/confirm/{unsubscribe_token}"
    text_body = (
        "Your daily disaster monitoring summary:\n\n"
        + "\n".join(summary_lines)
        + f"\n\nUnsubscribe: {unsub_link}"
    )
    html_body = digest_email(summary_lines, unsub_link)
    _send(email, "Your daily disaster monitoring digest", text_body, html_body)