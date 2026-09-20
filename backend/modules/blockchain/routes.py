from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db import async_session
from models import EventModel, DistributionRecordModel
from modules.blockchain.verify import verify_beneficiary

router = APIRouter(prefix="/api/blockchain", tags=["blockchain"])


class VerifyBeneficiaryRequest(BaseModel):
    event_id: str
    mock_id: str


@router.post("/verify-beneficiary")
async def verify_beneficiary_endpoint(payload: VerifyBeneficiaryRequest):
    # Confirm the event exists and is actually fund-eligible
    async with async_session() as session:
        result = await session.execute(
            select(EventModel).where(EventModel.event_id == payload.event_id)
        )
        event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    if len(payload.mock_id) < 4:
        raise HTTPException(status_code=400, detail="mock_id must be at least 4 characters")

    outcome = await verify_beneficiary(event_id=payload.event_id, mock_id=payload.mock_id)

    if outcome["status"] == "failed":
        raise HTTPException(status_code=500, detail=outcome.get("error", "Verification failed"))

    return outcome

@router.get("/dashboard")
async def dashboard():
    async with async_session() as session:
        result = await session.execute(
            select(EventModel)
            .where(EventModel.fund_status != "not_applicable")
            .order_by(EventModel.event_time.desc())
            .limit(100)
        )
        events = result.scalars().all()

        event_ids = [e.event_id for e in events]
        records_result = await session.execute(
            select(DistributionRecordModel).where(
                DistributionRecordModel.event_id.in_(event_ids)
            )
        )
        all_records = records_result.scalars().all()

    records_by_event = {}
    for r in all_records:
        records_by_event.setdefault(str(r.event_id), []).append({
            "record_id": str(r.record_id),
            "mock_id_last4": r.mock_id_last4,
            "status": r.status,
            "tx_hash": r.tx_hash,
        })

    return {
        "events": [
            {
                "event_id": str(e.event_id),
                "disaster_type": e.disaster_type,
                "region": e.region,
                "severity_tier": e.severity_tier,
                "fund_status": e.fund_status,
                "event_time": e.event_time.isoformat(),
                "beneficiaries_verified": len(
                    [r for r in records_by_event.get(str(e.event_id), []) if r["status"] == "verified"]
                ),
                "distribution_records": records_by_event.get(str(e.event_id), []),
            }
            for e in events
        ]
    }