# modules/notify/email_service.py

import os
import smtplib
from email.mime.text import MIMEText
from modules.notify.config import BASE_URL

SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]


def _send(to_email: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [to_email], msg.as_string())


async def send_confirmation_email(email: str, token: str):
    link = f"{BASE_URL}/subscribe/confirm/{token}"
    body = (
        f"Confirm your subscription to disaster alerts.\n\n"
        f"Click to confirm: {link}\n\n"
        f"If you didn't request this, ignore this email."
    )
    _send(email, "Confirm your disaster alert subscription", body)


async def send_prediction_alert(email: str, unsubscribe_token: str, disaster_type: str,
                                 region: str, risk_score: float, severity_tier: str):
    unsub_link = f"{BASE_URL}/subscribe/unsubscribe/{unsubscribe_token}"
    body = (
        f"Early warning: {disaster_type} risk detected in {region}\n"
        f"Severity: {severity_tier.upper()} (risk score: {risk_score:.2f})\n\n"
        f"This is an automated early-warning signal, not a confirmed event.\n\n"
        f"Unsubscribe: {unsub_link}"
    )
    _send(email, f"[Alert] {severity_tier.upper()} {disaster_type} risk — {region}", body)


async def send_daily_digest(email: str, unsubscribe_token: str, summary_lines: list[str]):
    unsub_link = f"{BASE_URL}/subscribe/unsubscribe/{unsubscribe_token}"
    body = (
        "Your daily disaster monitoring summary:\n\n"
        + "\n".join(summary_lines)
        + f"\n\nUnsubscribe: {unsub_link}"
    )
    _send(email, "Your daily disaster monitoring digest", body)