# modules/notify/routes.py

import secrets
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from db import async_session
from models import SubscriberModel
from modules.notify.templates import status_page
from modules.notify.email_service import send_confirmation_email, send_unsubscribe_link
from modules.notify.digest import run_digest_once


router = APIRouter(prefix="/subscribe", tags=["notifications"])


class SubscribeRequest(BaseModel):
    email: EmailStr
    region: str | None = None       # None = alerts for all regions
    disaster_type: str | None = None  # None = alerts for all disaster types


class UnsubscribeRequest(BaseModel):
    email: EmailStr


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
            # Normalize "" (sent by the frontend for "All regions" / "All
            # disaster types") to None. Downstream queries (notify.py,
            # digest.py) treat None as "match everything" but "" matches
            # nothing real — without this, "All" subscribers silently
            # never get alerted.
            region=payload.region or None,
            disaster_type=payload.disaster_type or None,
            confirm_token=secrets.token_urlsafe(24),
            unsubscribe_token=secrets.token_urlsafe(24),
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)

    await send_confirmation_email(sub.email, sub.confirm_token)
    return {"status": "pending_confirmation"}


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
            # Fresh token every time this is requested — invalidates any
            # previously issued unsubscribe token for this subscriber, so
            # an old email lying around can't be used later.
            sub.unsubscribe_token = secrets.token_urlsafe(24)
            await session.commit()
            await send_unsubscribe_link(sub.email, sub.unsubscribe_token)

    return {"status": "if_subscribed_link_sent"}


@router.get("/unsubscribe/confirm/{token}", response_class=HTMLResponse)
async def confirm_unsubscribe(token: str):
    async with async_session() as session:
        result = await session.execute(
            select(SubscriberModel).where(SubscriberModel.unsubscribe_token == token)
        )
        sub = result.scalar_one_or_none()
        if not sub:
            return HTMLResponse(
                status_page(title="Invalid token", message="This unsubscribe token is invalid or has already been used.", ok=False),
                status_code=404,
            )
        sub.is_active = False
        await session.commit()

    return HTMLResponse(status_page(
        title="Unsubscribed",
        message="You won't receive any more alerts from DisasterShield AI. If this was a mistake, you can subscribe again anytime.",
        ok=True,
    ))


@router.post("/digest-now")
async def digest_now():
    await run_digest_once()
    return {"status": "digest_triggered"}