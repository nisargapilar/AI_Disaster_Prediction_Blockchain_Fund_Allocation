"""
backend/modules/notify/digest.py

Sends a once-daily summary email to every confirmed, active subscriber,
regardless of severity — a "the system is alive" signal separate from
real-time high/critical alerts.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, or_

from db import async_session
from models import SubscriberModel, PredictionModel
from modules.notify.email_service import send_daily_digest
from modules.notify.config import DAILY_DIGEST_HOUR_UTC


async def fetch_predictions_today(session, disaster_type: str | None, region: str | None):
    # "Today" = since midnight UTC, not a rolling 24h window — so
    # triggering digest-now always pulls everything predicted so far
    # today, regardless of what time of day it's triggered.
    now = datetime.now(timezone.utc)
    cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)

    stmt = select(PredictionModel).where(PredictionModel.predicted_time >= cutoff)

    if disaster_type is not None:
        stmt = stmt.where(PredictionModel.disaster_type == disaster_type)
    if region is not None:
        stmt = stmt.where(PredictionModel.region == region)

    stmt = stmt.order_by(PredictionModel.predicted_time.desc())

    result = await session.execute(stmt)
    return result.scalars().all()


def build_summary_lines(predictions) -> list[str]:
    if not predictions:
        return ["No new predictions today for your subscription."]

    lines = []
    for p in predictions:
        lines.append(
            f"- {p.disaster_type.upper()} | {p.region} | "
            f"severity: {p.severity_tier} | risk_score: {p.risk_score:.2f} | "
            f"{p.predicted_time.strftime('%Y-%m-%d %H:%M UTC')}"
        )
    return lines


async def run_digest_once():
    async with async_session() as session:
        result = await session.execute(
            select(SubscriberModel).where(
                SubscriberModel.is_active == True,
                SubscriberModel.is_confirmed == True,
            )
        )
        subscribers = result.scalars().all()

        for sub in subscribers:
            predictions = await fetch_predictions_today(session, sub.disaster_type, sub.region)
            summary_lines = build_summary_lines(predictions)
            try:
                await send_daily_digest(sub.email, sub.unsubscribe_token, summary_lines)
            except Exception as e:
                print(f"[digest] Failed to email {sub.email}: {e}")

        print(f"[digest] Sent daily digest to {len(subscribers)} subscriber(s)")


def _seconds_until_next_run() -> float:
    now = datetime.now(timezone.utc)
    target = now.replace(hour=DAILY_DIGEST_HOUR_UTC, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def digest_loop():
    """Background task — sends the digest once per day at DAILY_DIGEST_HOUR_UTC."""
    while True:
        wait_seconds = _seconds_until_next_run()
        print(f"[digest] Next digest in {wait_seconds / 3600:.1f} hours")
        await asyncio.sleep(wait_seconds)
        try:
            await run_digest_once()
        except Exception as e:
            print(f"[digest] ERROR: {e}")