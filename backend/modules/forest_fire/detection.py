import httpx
import asyncio
import csv
import io
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from db import async_session
from models import EventModel
from modules.forest_fire.severity import compute_severity, is_fund_eligible
from modules.forest_fire.config import (
    FIRMS_MAP_KEY,
    FIRMS_SOURCE,
    FIRMS_AREA,
    FIRMS_DAY_RANGE,
    FIRMS_BASE_URL,
    POLL_INTERVAL_SECONDS,
)


def _make_external_id(row: dict) -> str:
    return (
        f"firms_{row['latitude']}_{row['longitude']}_"
        f"{row['acq_date']}_{row['acq_time']}_{row.get('satellite','')}"
    )


def _parse_event_time(acq_date: str, acq_time: str) -> datetime:
    acq_time_str = str(int(acq_time)).zfill(4)
    return datetime.strptime(
        f"{acq_date} {acq_time_str}",
        "%Y-%m-%d %H%M"
    ).replace(tzinfo=timezone.utc)


async def _fetch_firms_rows(area: str, day_range: str = FIRMS_DAY_RANGE):

    if not FIRMS_MAP_KEY:
        raise RuntimeError("FIRMS_MAP_KEY not set.")

    url = (
        f"{FIRMS_BASE_URL}/"
        f"{FIRMS_MAP_KEY}/"
        f"{FIRMS_SOURCE}/"
        f"{area}/"
        f"{day_range}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)

    text = response.text

    if text.strip().lower().startswith(("invalid", "error")):
        raise RuntimeError(text)

    return list(csv.DictReader(io.StringIO(text)))


def _build_event_model(row: dict) -> EventModel:

    confidence = row.get("confidence")
    frp = float(row.get("frp") or 0)

    tier, score = compute_severity(confidence, frp)

    lat = float(row["latitude"])
    lon = float(row["longitude"])

    return EventModel(

        disaster_type="forest_fire",
        source="real",

        external_id=_make_external_id(row),

        event_time=_parse_event_time(
            row["acq_date"],
            row["acq_time"]
        ),

        lat=lat,
        lon=lon,

        region=f"Lat {lat:.3f}, Lon {lon:.3f}",

        input_data={
            "brightness": float(
                row.get("bright_ti4")
                or row.get("brightness")
                or 0
            ),
            "frp": frp,
            "confidence": confidence,
            "satellite": row.get("satellite"),
            "instrument": row.get("instrument"),
            "daynight": row.get("daynight"),
        },

        risk_score=score,
        severity_tier=tier,

        fund_status=(
            "pending"
            if is_fund_eligible(tier)
            else "not_applicable"
        )
    )


async def fetch_and_process():

    try:
        rows = await _fetch_firms_rows(FIRMS_AREA)

    except RuntimeError as e:
        print(e)
        return

    async with async_session() as session:

        for row in rows:

            db_row = _build_event_model(row)

            session.add(db_row)

            try:

                await session.commit()

                print(
                    f"New forest fire detected -> "
                    f"{db_row.region}"
                )

            except IntegrityError:

                await session.rollback()


async def detect_now(
    lat: float,
    lon: float,
    radius_deg: float = 0.5
):

    print("\n===========================")
    print("FOREST FIRE DETECTION")
    print("===========================")

    west = lon - radius_deg
    south = lat - radius_deg
    east = lon + radius_deg
    north = lat + radius_deg

    area = f"{west},{south},{east},{north}"

    print("Searching:", area)

    rows = await _fetch_firms_rows(area, "1")

    print("Hotspots Found:", len(rows))

    from modules.forest_fire.routes import serialize

    # ====================================================
    # NO FIRE FOUND
    # ====================================================

    if len(rows) == 0:

        print("No hotspot found.")

        safe_event = EventModel(

            disaster_type="forest_fire",

            source="real",

            external_id=f"safe_{datetime.now(timezone.utc).timestamp()}",

            event_time=datetime.now(timezone.utc),

            lat=lat,
            lon=lon,

            region=f"Lat {lat:.3f}, Lon {lon:.3f}",

            input_data={
                "status": "SAFE",
                "message": "No active forest fire detected",
                "brightness": 0,
                "frp": 0,
                "confidence": "none",
                "satellite": "NASA FIRMS",
                "instrument": "VIIRS",
                "daynight": "-"
            },

            risk_score=0.0,

            severity_tier="low",

            fund_status="not_applicable"

        )

        async with async_session() as session:

            session.add(safe_event)

            await session.commit()

            await session.refresh(safe_event)

        print("SAFE record inserted.")

        return [serialize(safe_event)]

    # ====================================================
    # HOTSPOTS FOUND
    # ====================================================

    inserted = []

    async with async_session() as session:

        for row in rows:

            db_row = _build_event_model(row)

            session.add(db_row)

            try:

                await session.commit()

                await session.refresh(db_row)

                print(
                    f"REAL FIRE INSERTED -> "
                    f"{db_row.region}"
                )

                inserted.append(db_row)

            except IntegrityError:

                await session.rollback()

                print("Duplicate hotspot skipped.")

    return [serialize(x) for x in inserted]


async def start_polling():

    while True:

        try:

            await fetch_and_process()

        except Exception as e:

            print("Forest Fire Poll Error:", e)

        await asyncio.sleep(POLL_INTERVAL_SECONDS)