# modules/notify/routes.py

import secrets
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from db import async_session
from models import SubscriberModel
from modules.notify.email_service import send_confirmation_email

router = APIRouter(prefix="/subscribe", tags=["notifications"])


class SubscribeRequest(BaseModel):
    email: EmailStr
    region: str | None = None       # None = alerts for all regions
    disaster_type: str | None = None  # None = alerts for all disaster types


@router.post("")
async def subscribe(payload: SubscribeRequest):
    async with async_session() as session:
        existing = await session.execute(
            select(SubscriberModel).where(SubscriberModel.email == payload.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(400, "Email already subscribed.")

        sub = SubscriberModel(
            email=payload.email,
            region=payload.region,
            disaster_type=payload.disaster_type,
            confirm_token=secrets.token_urlsafe(24),
            unsubscribe_token=secrets.token_urlsafe(24),
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)

    await send_confirmation_email(sub.email, sub.confirm_token)
    return {"status": "pending_confirmation"}


@router.get("/confirm/{token}")
async def confirm(token: str):
    async with async_session() as session:
        result = await session.execute(
            select(SubscriberModel).where(SubscriberModel.confirm_token == token)
        )
        sub = result.scalar_one_or_none()
        if not sub:
            raise HTTPException(404, "Invalid confirmation link.")
        sub.is_confirmed = True
        await session.commit()
    return {"status": "confirmed"}


@router.get("/unsubscribe/{token}")
async def unsubscribe(token: str):
    async with async_session() as session:
        result = await session.execute(
            select(SubscriberModel).where(SubscriberModel.unsubscribe_token == token)
        )
        sub = result.scalar_one_or_none()
        if not sub:
            raise HTTPException(404, "Invalid unsubscribe link.")
        sub.is_active = False
        await session.commit()
    return {"status": "unsubscribed"}