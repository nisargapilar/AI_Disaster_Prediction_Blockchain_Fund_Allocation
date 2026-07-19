import httpx
import asyncio
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from db import async_session
from models import EventModel
from modules.earthquake.severity import compute_severity, is_fund_eligible
from modules.earthquake.config import USGS_FEED_URL, POLL_INTERVAL_SECONDS

async def fetch_and_process():
    async with httpx.AsyncClient() as client:
        resp = await client.get(USGS_FEED_URL, timeout=10)
        data = resp.json()

    async with async_session() as session:
        for feature in data.get("features", []):
            usgs_id = feature["id"]
            props = feature["properties"]
            lon, lat, depth = feature["geometry"]["coordinates"]
            magnitude = props.get("mag") or 0.0
            tier, score = compute_severity(magnitude)
            event_time = datetime.fromtimestamp(props["time"] / 1000, tz=timezone.utc)

            row = EventModel(
                disaster_type="earthquake",
                source="real",
                external_id=usgs_id,
                event_time=event_time,
                lat=lat,
                lon=lon,
                region=props.get("place", "unknown"),
                input_data={"magnitude": magnitude, "depth": depth, "place": props.get("place")},
                risk_score=score,
                severity_tier=tier,
                fund_status="pending" if is_fund_eligible(tier) else "not_applicable",
            )
            session.add(row)
            try:
                await session.commit()
                print(f"New earthquake detected: {row.region} M{magnitude} ({tier})")
            except IntegrityError:
                await session.rollback()  # already seen this event

async def start_polling():
    while True:
        try:
            await fetch_and_process()
        except Exception as e:
            print("Earthquake poll error:", e)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)