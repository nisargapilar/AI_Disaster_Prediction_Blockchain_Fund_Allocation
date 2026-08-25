from fastapi import APIRouter
from datetime import datetime, timezone
from sqlalchemy import select

from db import async_session
from models import EventModel , PredictionModel
from modules.earthquake.severity import compute_severity, is_fund_eligible
from modules.earthquake.prediction import run_prediction_once

router = APIRouter(prefix="/earthquake", tags=["earthquake"])


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
    }

@router.get("/detected-earthquake-events")
async def detected_earthquake_events():
    async with async_session() as session:
        result = await session.execute(
            select(EventModel)
            .where(EventModel.disaster_type == "earthquake")
            .order_by(EventModel.event_time.desc())
            .limit(50)
        )
        return [serialize(r) for r in result.scalars().all()]

@router.post("/simulate-detection")
async def simulate_detection(magnitude: float, lat: float, lon: float, region: str = "Simulated Region"):
    tier, score = compute_severity(magnitude)
    row = EventModel(
        disaster_type="earthquake",
        source="simulated",
        external_id=None,
        event_time=datetime.now(timezone.utc),
        lat=lat,
        lon=lon,
        region=region,
        input_data={"magnitude": magnitude, "depth": 10.0, "place": region},
        risk_score=score,
        severity_tier=tier,
        fund_status="pending" if is_fund_eligible(tier) else "not_applicable",
        created_at=datetime.now(timezone.utc),
    )
    async with async_session() as session:
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return serialize(row)




def serialize_prediction(row: PredictionModel):
    return {
        "prediction_id": str(row.prediction_id),
        "disaster_type": row.disaster_type,
        "region": row.region,
        "predicted_time": row.predicted_time.isoformat(),
        "input_data": row.input_data,
        "risk_score": row.risk_score,
        "severity_tier": row.severity_tier,
        "is_simulated": row.is_simulated,
    }


@router.get("/predicted-earthquake-events")
async def predicted_earthquake_events():
    async with async_session() as session:
        result = await session.execute(
            select(PredictionModel)
            .where(PredictionModel.disaster_type == "earthquake")
            .order_by(PredictionModel.predicted_time.desc())
            .limit(50)
        )
        return [serialize_prediction(r) for r in result.scalars().all()]


@router.post("/simulate-prediction")
async def simulate_prediction():
    await run_prediction_once()
    return {"status": "prediction_triggered"}