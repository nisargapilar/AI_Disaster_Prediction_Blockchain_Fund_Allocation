import asyncio
from datetime import datetime, timezone
from db import async_session
from models import EventModel

async def main():
    async with async_session() as session:
        event = EventModel(
            disaster_type="earthquake",
            source="simulated",
            external_id="test_mangalore_001",
            event_time=datetime.now(timezone.utc),
            lat=12.91,
            lon=74.86,
            region="Mangalore, India (test)",
            input_data={"magnitude": 6.2, "note": "manual test insert"},
            risk_score=0.85,
            severity_tier="critical",
            fund_status="pending",
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        print("Inserted test event:")
        print("  event_id:", event.event_id)
        print("  region:", event.region)
        print("  fund_status:", event.fund_status)

asyncio.run(main())