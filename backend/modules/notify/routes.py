# modules/notify/routes.py

import secrets
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from fastapi.responses import HTMLResponse
from modules.notify.templates import status_page

from db import async_session
from models import SubscriberModel
from modules.notify.email_service import send_confirmation_email
from modules.notify.digest import run_digest_once
from modules.notify.email_service import send_confirmation_email, send_unsubscribe_link


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

@router.post("/digest-now")
async def digest_now():
    await run_digest_once()
    return {"status": "digest_triggered"}


class UnsubscribeRequest(BaseModel):
    email: EmailStr


@router.post("/unsubscribe-request")
async def request_unsubscribe_link(payload: UnsubscribeRequest):
    async with async_session() as session:
        result = await session.execute(
            select(SubscriberModel).where(SubscriberModel.email == payload.email)
        )
        sub = result.scalar_one_or_none()

    # Always return the same response whether or not the email exists —
    # otherwise this endpoint becomes a way to check who's subscribed.
    if sub and sub.is_active:
        await send_unsubscribe_link(sub.email, sub.unsubscribe_token)

    return {"status": "if_subscribed_link_sent"}


@router.get("/confirm/{token}", response_class=HTMLResponse)
async def confirm(token: str):
    async with async_session() as session:
        result = await session.execute(
            select(SubscriberModel).where(SubscriberModel.confirm_token == token)
        )
        sub = result.scalar_one_or_none()
        if not sub:
            return HTMLResponse(
                status_page(title="Invalid link", message="This confirmation link is invalid or has already been used.", ok=False),
                status_code=404,
            )
        sub.is_confirmed = True
        await session.commit()

    return HTMLResponse(status_page(
        title="Subscription confirmed",
        message="You're all set. You'll receive email alerts when risk crosses the threshold for your selected region and disaster type.",
        ok=True,
    ))


@router.get("/unsubscribe/{token}", response_class=HTMLResponse)
async def unsubscribe(token: str):
    async with async_session() as session:
        result = await session.execute(
            select(SubscriberModel).where(SubscriberModel.unsubscribe_token == token)
        )
        sub = result.scalar_one_or_none()
        if not sub:
            return HTMLResponse(
                status_page(title="Invalid link", message="This unsubscribe link is invalid or has already been used.", ok=False),
                status_code=404,
            )
        sub.is_active = False
        await session.commit()

    return HTMLResponse(status_page(
        title="Unsubscribed",
        message="You won't receive any more alerts from DisasterShield AI. If this was a mistake, you can subscribe again anytime.",
        ok=True,
    ))