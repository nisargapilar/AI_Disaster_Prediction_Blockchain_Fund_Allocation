from fastapi import APIRouter
from datetime import datetime, timezone
from sqlalchemy import select

from db import async_session
from models import EventModel
from modules.forest_fire.severity import compute_severity, is_fund_eligible
from modules.forest_fire import detection

router = APIRouter(prefix="/forest_fire", tags=["forest_fire"])


def serialize(row: EventModel):
    return {
        "event_id": str(row.event_id),
        "disaster_type": row.disaster_type,
        "source": row.source,
        "event_time": row.event_time.isoformat(),
        "location": {"lat": row.lat, "lon": row.lon, "region": row.region},
        "input_data": row.input_data,
        "risk_score": row.risk_score,
        "severity_tier": row.severity_tier,
        "fund_status": row.fund_status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/events")
async def get_events():
    async with async_session() as session:
        result = await session.execute(
            select(EventModel)
            .where(EventModel.disaster_type == "forest_fire")
            .order_by(EventModel.event_time.desc())
            .limit(50)
        )
        return [serialize(r) for r in result.scalars().all()]


# --------------------------------------------------
# ON-DEMAND REAL DETECTION (NASA FIRMS)
# GET /forest_fire/detect?lat=..&lon=..
# Checks a small area around the given point RIGHT NOW, instead of
# waiting for the background poller's next cycle.
# --------------------------------------------------
@router.get("/detect")
async def detect(lat: float, lon: float, radius: float = 0.5):

    print("DETECT ROUTE CALLED")

    events = await detection.detect_now(lat, lon, radius)

    return events


@router.post("/simulate")
async def simulate(confidence: str = "high", frp: float = 80.0,
                    lat: float = 15.3173, lon: float = 75.7139,
                    region: str = "Simulated Forest Block"):
    tier, score = compute_severity(confidence, frp)
    row = EventModel(
        disaster_type="forest_fire",
        source="simulated",
        external_id=None,
        event_time=datetime.now(timezone.utc),
        lat=lat,
        lon=lon,
        region=region,
        input_data={
            "brightness": 400.0,
            "frp": frp,
            "confidence": confidence,
            "satellite": "SIMULATED",
            "instrument": "SIMULATED",
            "daynight": "D",
        },
        risk_score=score,
        severity_tier=tier,
        fund_status="pending" if is_fund_eligible(tier) else "not_applicable",
    )
    async with async_session() as session:
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return serialize(row)