from sqlalchemy import select, or_
from models import SubscriberModel
from modules.notify.email_service import send_prediction_alert


async def notify_subscribers(session, disaster_type: str, region: str,
                              risk_score: float, severity_tier: str):
    stmt = select(SubscriberModel).where(
        SubscriberModel.is_active == True,
        SubscriberModel.is_confirmed == True,
        or_(SubscriberModel.disaster_type == disaster_type, SubscriberModel.disaster_type.is_(None)),
        or_(SubscriberModel.region == region, SubscriberModel.region.is_(None)),
    )
    result = await session.execute(stmt)
    subscribers = result.scalars().all()

    for sub in subscribers:
        try:
            await send_prediction_alert(
                sub.email, sub.unsubscribe_token, disaster_type, region, risk_score, severity_tier
            )
        except Exception as e:
            print(f"[notify] Failed to email {sub.email}: {e}")

    print(f"[notify] Alerted {len(subscribers)} subscriber(s) for {disaster_type}/{region}")