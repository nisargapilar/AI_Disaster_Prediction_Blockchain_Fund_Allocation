from fastapi import APIRouter
from sqlalchemy import select

from db import async_session
from models import EventModel
from modules.flood.detection import predict_flood

router = APIRouter(
    prefix="/flood",
    tags=["Flood"],
)


def serialize(row):
    return {
        "event_id": str(row.event_id),
        "disaster_type": row.disaster_type,
        "source": row.source,
        "event_time": row.event_time.isoformat(),
        "location": {
            "lat": row.lat,
            "lon": row.lon,
            "region": row.region,
        },
        "input_data": row.input_data,
        "risk_score": row.risk_score,
        "severity_tier": row.severity_tier,
        "fund_status": row.fund_status,
    }


@router.get("/events")
async def get_events():
    async with async_session() as session:
        result = await session.execute(
            select(EventModel)
            .where(EventModel.disaster_type == "flood")
            .order_by(EventModel.event_time.desc())
            .limit(50)
        )

        return [
            serialize(row)
            for row in result.scalars().all()
        ]


@router.post("/predict")
async def predict(
    rainfall: float,
    humidity: float,
    temperature: float,
    lat: float,
    lon: float,
    region: str,
):
    row = await predict_flood(
        rainfall=rainfall,
        humidity=humidity,
        temperature=temperature,
        lat=lat,
        lon=lon,
        region=region,
    )

    return serialize(row)