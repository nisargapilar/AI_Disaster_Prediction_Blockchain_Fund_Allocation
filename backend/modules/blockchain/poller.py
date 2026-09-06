import asyncio
from sqlalchemy import select
from db import async_session
from models import EventModel
from modules.blockchain.release import trigger_fund_release
from modules.blockchain.config import (
    MANGALORE_LAT, MANGALORE_LON, MANGALORE_RADIUS_DEG, POLL_INTERVAL_SECONDS,
)


def is_in_mangalore(lat: float, lon: float) -> bool:
    return (
        abs(lat - MANGALORE_LAT) <= MANGALORE_RADIUS_DEG
        and abs(lon - MANGALORE_LON) <= MANGALORE_RADIUS_DEG
    )


async def process_pending_events():
    async with async_session() as session:
        result = await session.execute(
            select(EventModel).where(EventModel.fund_status == "pending")
        )
        pending_events = result.scalars().all()

        for event in pending_events:
            if not is_in_mangalore(event.lat, event.lon):
                continue  # leave as "pending" — out of scope for this demo

            outcome = trigger_fund_release(
                event_id=str(event.event_id),
                disaster_type=event.disaster_type,
                region=event.region,
            )

            event.fund_status = "released" if outcome["status"] == "released" else "failed"
            await session.commit()


async def start_polling():
    print("Blockchain fund-release poller started (Mangalore-only)")
    while True:
        try:
            await process_pending_events()
        except Exception as e:
            print("Blockchain poller error:", e)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        