import httpx
import asyncio
import csv
import io
import os
import joblib
import pandas as pd

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from db import async_session
from models import EventModel

from modules.forest_fire.severity import (
    compute_severity,
    is_fund_eligible
)

from modules.forest_fire.config import (
    FIRMS_MAP_KEY,
    FIRMS_SOURCE,
    FIRMS_AREA,
    FIRMS_DAY_RANGE,
    FIRMS_BASE_URL,
    POLL_INTERVAL_SECONDS,
)


# ============================================================
# 0. FOREST FIRE ML MODEL
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

FORESTFIRE_ARTIFACT_DIR = os.path.join(
    BASE_DIR,
    "ml_artifacts",
    "forestfire_artifacts"
)

FORESTFIRE_MODEL_PATH = os.path.join(
    FORESTFIRE_ARTIFACT_DIR,
    "forestfire_xgboost.pkl"
)

FORESTFIRE_IMPUTER_PATH = os.path.join(
    FORESTFIRE_ARTIFACT_DIR,
    "forestfire_imputer.pkl"
)

FORESTFIRE_ENCODER_PATH = os.path.join(
    FORESTFIRE_ARTIFACT_DIR,
    "forestfire_label_encoder.pkl"
)


# ============================================================
# LOAD TRAINED ML ARTIFACTS
# ============================================================

forestfire_model = joblib.load(
    FORESTFIRE_MODEL_PATH
)

forestfire_imputer = joblib.load(
    FORESTFIRE_IMPUTER_PATH
)

forestfire_label_encoder = joblib.load(
    FORESTFIRE_ENCODER_PATH
)


print(
    "Forest Fire XGBoost model loaded successfully."
)

print(
    "Forest Fire ML features:",
    list(
        forestfire_imputer.feature_names_in_
    )
)

print(
    "Forest Fire classes:",
    list(
        forestfire_label_encoder.classes_
    )
)

print(
    "Forest Fire number of features:",
    forestfire_model.n_features_in_
)


# ============================================================
# IMPORTANT
# Existing database records may have been created before
# ML prediction was added.
#
# True  -> Recalculate ML prediction for existing records
# False -> Keep existing database values
# ============================================================

RECALCULATE_EXISTING_ML = True


# ============================================================
# 1. CREATE UNIQUE FIRMS EVENT ID
# ============================================================

def _make_external_id(row: dict) -> str:

    return (
        f"firms_{row['latitude']}_"
        f"{row['longitude']}_"
        f"{row['acq_date']}_"
        f"{row['acq_time']}_"
        f"{row.get('satellite', '')}"
    )


# ============================================================
# 2. PARSE FIRMS EVENT TIME
# ============================================================

def _parse_event_time(
    acq_date: str,
    acq_time: str
) -> datetime:

    acq_time_str = str(
        int(float(acq_time))
    ).zfill(4)

    return datetime.strptime(
        f"{acq_date} {acq_time_str}",
        "%Y-%m-%d %H%M"
    ).replace(
        tzinfo=timezone.utc
    )


# ============================================================
# 3. CONVERT FIRMS CONFIDENCE TO NUMERIC VALUE
# ============================================================

def _parse_confidence(value):

    """
    Convert NASA FIRMS confidence into numeric value.

    Numeric values:
        0 - 100

    FIRMS text:
        low
        nominal
        medium
        high

    FIRMS short codes:
        l = low
        n = nominal
        h = high
    """

    if value is None:
        return 0.0

    # --------------------------------------------------------
    # Already numeric
    # --------------------------------------------------------

    try:

        return float(value)

    except (
        ValueError,
        TypeError
    ):

        pass

    # --------------------------------------------------------
    # Convert to lowercase text
    # --------------------------------------------------------

    confidence_text = str(
        value
    ).strip().lower()

    # --------------------------------------------------------
    # FIRMS mapping
    # --------------------------------------------------------

    confidence_mapping = {

        "low": 30.0,
        "nominal": 60.0,
        "medium": 60.0,
        "high": 90.0,

        "l": 30.0,
        "n": 60.0,
        "h": 90.0
    }

    return confidence_mapping.get(
        confidence_text,
        0.0
    )


# ============================================================
# 4. XGBOOST FOREST FIRE PREDICTION
# ============================================================

def _predict_forestfire_ml(
    latitude,
    longitude,
    brightness,
    scan,
    track,
    confidence,
    bright_t31,
    daynight_encoded,
    month,
    day_of_year,
    fire_type
):

    """
    Predict forest fire severity using trained XGBoost.

    EXACT 11 FEATURES USED DURING TRAINING:

        1. latitude
        2. longitude
        3. brightness
        4. scan
        5. track
        6. confidence
        7. bright_t31
        8. daynight_encoded
        9. month
        10. day_of_year
        11. type
    """

    feature_names = [

        "latitude",
        "longitude",
        "brightness",
        "scan",
        "track",
        "confidence",
        "bright_t31",
        "daynight_encoded",
        "month",
        "day_of_year",
        "type"

    ]

    # --------------------------------------------------------
    # Create DataFrame
    # --------------------------------------------------------

    features = pd.DataFrame(
        [[
            latitude,
            longitude,
            brightness,
            scan,
            track,
            confidence,
            bright_t31,
            daynight_encoded,
            month,
            day_of_year,
            fire_type
        ]],
        columns=feature_names
    )

    # --------------------------------------------------------
    # Make sure feature order matches training
    # --------------------------------------------------------

    features = features[
        list(
            forestfire_imputer.feature_names_in_
        )
    ]

    # --------------------------------------------------------
    # Apply trained imputer
    # --------------------------------------------------------

    features_imputed = (
        forestfire_imputer.transform(
            features
        )
    )

    # --------------------------------------------------------
    # XGBoost prediction
    # --------------------------------------------------------

    raw_prediction = (
        forestfire_model.predict(
            features_imputed
        )[0]
    )

    # --------------------------------------------------------
    # Convert encoded prediction to severity label
    # --------------------------------------------------------

    predicted_severity = (
        forestfire_label_encoder.inverse_transform(
            [int(raw_prediction)]
        )[0]
    )

    # --------------------------------------------------------
    # Prediction probabilities
    # --------------------------------------------------------

    probabilities = (
        forestfire_model.predict_proba(
            features_imputed
        )[0]
    )

    # --------------------------------------------------------
    # Maximum confidence
    # --------------------------------------------------------

    max_confidence = float(
        probabilities.max()
    )

    # --------------------------------------------------------
    # Probability dictionary
    # --------------------------------------------------------

    probability_dict = {

        str(class_name): float(
            probability
        )

        for class_name, probability
        in zip(
            forestfire_label_encoder.classes_,
            probabilities
        )
    }

    # --------------------------------------------------------
    # Display prediction
    # --------------------------------------------------------

    print(
        "\n=========================================="
    )

    print(
        "FOREST FIRE XGBOOST PREDICTION"
    )

    print(
        "=========================================="
    )

    print(
        "INPUT FEATURES:"
    )

    print(
        features.to_dict(
            orient="records"
        )[0]
    )

    print(
        "RAW PREDICTION:",
        int(raw_prediction)
    )

    print(
        "PREDICTED SEVERITY:",
        predicted_severity
    )

    print(
        "PROBABILITIES:",
        probabilities
    )

    print(
        "PROBABILITY DICTIONARY:",
        probability_dict
    )

    print(
        "CLASS ORDER:",
        list(
            forestfire_label_encoder.classes_
        )
    )

    print(
        "MAX CONFIDENCE:",
        max_confidence
    )

    print(
        "=========================================="
    )

    return (
        predicted_severity,
        max_confidence,
        probability_dict
    )


# ============================================================
# 5. FETCH NASA FIRMS DATA
# ============================================================

async def _fetch_firms_rows(
    area: str,
    day_range: str = FIRMS_DAY_RANGE
):

    if not FIRMS_MAP_KEY:

        raise RuntimeError(
            "FIRMS_MAP_KEY not set."
        )

    url = (
        f"{FIRMS_BASE_URL}/"
        f"{FIRMS_MAP_KEY}/"
        f"{FIRMS_SOURCE}/"
        f"{area}/"
        f"{day_range}"
    )

    async with httpx.AsyncClient() as client:

        response = await client.get(
            url,
            timeout=30
        )

    response.raise_for_status()

    text = response.text

    if text.strip().lower().startswith(
        (
            "invalid",
            "error"
        )
    ):

        raise RuntimeError(
            text
        )

    return list(
        csv.DictReader(
            io.StringIO(text)
        )
    )


# ============================================================
# 6. EXTRACT FIRMS FEATURES
# ============================================================

def _extract_forestfire_features(
    row: dict
):
    """
    Convert one NASA FIRMS row into the exact
    11 features required by XGBoost.
    """

    # --------------------------------------------------------
    # Coordinates
    # --------------------------------------------------------

    lat = float(
        row["latitude"]
    )

    lon = float(
        row["longitude"]
    )

    # --------------------------------------------------------
    # Event time
    # --------------------------------------------------------

    event_time = _parse_event_time(
        row["acq_date"],
        row["acq_time"]
    )

    # --------------------------------------------------------
    # Date features
    # --------------------------------------------------------

    month = event_time.month

    day_of_year = (
        event_time.timetuple().tm_yday
    )

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    raw_confidence = row.get(
        "confidence"
    )

    confidence = _parse_confidence(
        raw_confidence
    )

    # --------------------------------------------------------
    # Brightness
    # --------------------------------------------------------

    try:

        brightness = float(
            row.get("brightness")
            or row.get("bright_ti4")
            or 0
        )

    except (
        ValueError,
        TypeError
    ):

        brightness = 0.0

    # --------------------------------------------------------
    # Scan
    # --------------------------------------------------------

    try:

        scan = float(
            row.get("scan")
            or 0
        )

    except (
        ValueError,
        TypeError
    ):

        scan = 0.0

    # --------------------------------------------------------
    # Track
    # --------------------------------------------------------

    try:

        track = float(
            row.get("track")
            or 0
        )

    except (
        ValueError,
        TypeError
    ):

        track = 0.0

    # --------------------------------------------------------
    # Brightness temperature
    # --------------------------------------------------------

    try:

        bright_t31 = float(
            row.get("bright_t31")
            or 0
        )

    except (
        ValueError,
        TypeError
    ):

        bright_t31 = 0.0

    # --------------------------------------------------------
    # Day / Night
    # --------------------------------------------------------

    daynight = str(
        row.get("daynight")
        or "N"
    ).strip().upper()

    if daynight == "D":

        daynight_encoded = 1

    else:

        daynight_encoded = 0

    # --------------------------------------------------------
    # FIRMS type
    # --------------------------------------------------------

    try:

        fire_type = int(
            float(
                row.get("type")
                or 0
            )
        )

    except (
        ValueError,
        TypeError
    ):

        fire_type = 0

    # --------------------------------------------------------
    # FRP
    # --------------------------------------------------------

    try:

        frp = float(
            row.get("frp")
            or 0
        )

    except (
        ValueError,
        TypeError
    ):

        frp = 0.0

    return {

        "latitude": lat,

        "longitude": lon,

        "brightness": brightness,

        "scan": scan,

        "track": track,

        "confidence": confidence,

        "bright_t31": bright_t31,

        "daynight_encoded": daynight_encoded,

        "month": month,

        "day_of_year": day_of_year,

        "type": fire_type,

        "frp": frp,

        "raw_confidence": raw_confidence,

        "daynight": daynight,

        "event_time": event_time

    }


# ============================================================
# 7. BUILD EVENT MODEL
# ============================================================

def _build_event_model(
    row: dict
) -> EventModel:

    data = _extract_forestfire_features(
        row
    )

    # --------------------------------------------------------
    # Get features
    # --------------------------------------------------------

    lat = data["latitude"]
    lon = data["longitude"]

    brightness = data["brightness"]
    scan = data["scan"]
    track = data["track"]

    confidence = data["confidence"]

    bright_t31 = data["bright_t31"]

    daynight_encoded = (
        data["daynight_encoded"]
    )

    month = data["month"]

    day_of_year = data["day_of_year"]

    fire_type = data["type"]

    frp = data["frp"]

    raw_confidence = (
        data["raw_confidence"]
    )

    daynight = data["daynight"]

    event_time = data["event_time"]

    # ========================================================
    # XGBOOST PREDICTION
    # ========================================================

    (
        ml_severity,
        ml_confidence,
        ml_probability_dict
    ) = _predict_forestfire_ml(

        latitude=lat,

        longitude=lon,

        brightness=brightness,

        scan=scan,

        track=track,

        confidence=confidence,

        bright_t31=bright_t31,

        daynight_encoded=daynight_encoded,

        month=month,

        day_of_year=day_of_year,

        fire_type=fire_type

    )

    # ========================================================
    # RULE-BASED RISK SCORE
    #
    # This is kept separately from ML severity.
    # ========================================================

    _, rule_based_score = compute_severity(
        raw_confidence,
        frp
    )

    # ========================================================
    # CREATE EVENT
    # ========================================================

    return EventModel(

        disaster_type="forest_fire",

        source="real",

        external_id=_make_external_id(
            row
        ),

        event_time=event_time,

        lat=lat,

        lon=lon,

        region=(
            f"Lat {lat:.3f}, "
            f"Lon {lon:.3f}"
        ),

        # ====================================================
        # INPUT DATA
        # ====================================================

        input_data={

            # ------------------------------------------------
            # EXACT 11 XGBOOST FEATURES
            # ------------------------------------------------

            "latitude": lat,

            "longitude": lon,

            "brightness": brightness,

            "scan": scan,

            "track": track,

            "confidence": confidence,

            "bright_t31": bright_t31,

            "daynight_encoded": daynight_encoded,

            "month": month,

            "day_of_year": day_of_year,

            "type": fire_type,

            # ------------------------------------------------
            # FIRMS DATA
            # ------------------------------------------------

            "frp": frp,

            "raw_confidence": raw_confidence,

            "daynight": daynight,

            "satellite": row.get(
                "satellite"
            ),

            "instrument": row.get(
                "instrument"
            ),

            # ------------------------------------------------
            # ML RESULT
            # ------------------------------------------------

            "ml_prediction": ml_severity,

            "ml_confidence": ml_confidence,

            "ml_probabilities": ml_probability_dict

        },

        # ----------------------------------------------------
        # Risk score
        # ----------------------------------------------------

        risk_score=rule_based_score,

        # ----------------------------------------------------
        # IMPORTANT:
        # Severity comes from XGBoost
        # ----------------------------------------------------

        severity_tier=ml_severity,

        # ----------------------------------------------------
        # Fund eligibility uses ML severity
        # ----------------------------------------------------

        fund_status=(

            "pending"

            if is_fund_eligible(
                ml_severity
            )

            else "not_applicable"

        )

    )


# ============================================================
# 8. UPDATE EXISTING EVENT WITH ML PREDICTION
# ============================================================

def _update_existing_event_with_ml(
    existing_event: EventModel,
    row: dict
):

    """
    Recalculate ML prediction for an existing
    FIRMS database event.

    This is important because old records may
    have severity_tier='medium' from the old
    rule-based system.
    """

    data = _extract_forestfire_features(
        row
    )

    (
        ml_severity,
        ml_confidence,
        ml_probability_dict
    ) = _predict_forestfire_ml(

        latitude=data["latitude"],

        longitude=data["longitude"],

        brightness=data["brightness"],

        scan=data["scan"],

        track=data["track"],

        confidence=data["confidence"],

        bright_t31=data["bright_t31"],

        daynight_encoded=data[
            "daynight_encoded"
        ],

        month=data["month"],

        day_of_year=data[
            "day_of_year"
        ],

        fire_type=data["type"]

    )

    # --------------------------------------------------------
    # Keep rule-based risk score separate
    # --------------------------------------------------------

    _, rule_based_score = compute_severity(
        data["raw_confidence"],
        data["frp"]
    )

    # --------------------------------------------------------
    # Update input_data
    # --------------------------------------------------------

    current_input_data = (
        dict(
            existing_event.input_data
            or {}
        )
    )

    # 11 ML features

    current_input_data.update({

        "latitude": data["latitude"],

        "longitude": data["longitude"],

        "brightness": data["brightness"],

        "scan": data["scan"],

        "track": data["track"],

        "confidence": data["confidence"],

        "bright_t31": data["bright_t31"],

        "daynight_encoded": data[
            "daynight_encoded"
        ],

        "month": data["month"],

        "day_of_year": data[
            "day_of_year"
        ],

        "type": data["type"],

        # FIRMS information

        "frp": data["frp"],

        "raw_confidence": data[
            "raw_confidence"
        ],

        "daynight": data["daynight"],

        "satellite": row.get(
            "satellite"
        ),

        "instrument": row.get(
            "instrument"
        ),

        # ML output

        "ml_prediction": ml_severity,

        "ml_confidence": ml_confidence,

        "ml_probabilities": (
            ml_probability_dict
        )

    })

    existing_event.input_data = (
        current_input_data
    )

    existing_event.risk_score = (
        rule_based_score
    )

    existing_event.severity_tier = (
        ml_severity
    )

    existing_event.fund_status = (

        "pending"

        if is_fund_eligible(
            ml_severity
        )

        else "not_applicable"

    )

    return existing_event


# ============================================================
# 9. FETCH AND PROCESS FIRE EVENTS
# ============================================================

async def fetch_and_process():

    try:

        rows = await _fetch_firms_rows(
            FIRMS_AREA
        )

    except Exception as e:

        print(
            "FIRMS Fetch Error:",
            e
        )

        return

    print(
        f"FIRMS rows received: {len(rows)}"
    )

    async with async_session() as session:

        for row in rows:

            external_id = (
                _make_external_id(row)
            )

            try:

                result = await session.execute(

                    select(
                        EventModel
                    ).where(

                        EventModel.external_id
                        == external_id

                    )

                )

                existing_event = (
                    result.scalar_one_or_none()
                )

                # ------------------------------------------------
                # Existing event
                # ------------------------------------------------

                if existing_event is not None:

                    if RECALCULATE_EXISTING_ML:

                        print(
                            "\nUpdating existing FIRMS event with XGBoost -> "
                            f"{existing_event.region}"
                        )

                        _update_existing_event_with_ml(
                            existing_event,
                            row
                        )

                        await session.commit()

                        print(
                            "Updated ML severity -> "
                            f"{existing_event.severity_tier}"
                        )

                    else:

                        print(
                            "Existing FIRMS event skipped -> "
                            f"{existing_event.region}"
                        )

                    continue

                # ------------------------------------------------
                # New event
                # ------------------------------------------------

                db_row = _build_event_model(
                    row
                )

                session.add(
                    db_row
                )

                await session.commit()

                print(
                    "\nNew forest fire detected -> "
                    f"{db_row.region}"
                )

                print(
                    "ML severity -> "
                    f"{db_row.severity_tier}"
                )

            except IntegrityError:

                await session.rollback()

                print(
                    "Duplicate FIRMS event skipped."
                )

            except Exception as e:

                await session.rollback()

                print(
                    "Error processing FIRMS event:",
                    e
                )


# ============================================================
# 10. DETECT FIRE NOW
# ============================================================

async def detect_now(
    lat: float,
    lon: float,
    radius_deg: float = 0.5
):

    print(
        "\n==========================="
    )

    print(
        "FOREST FIRE DETECTION"
    )

    print(
        "==========================="
    )

    # --------------------------------------------------------
    # Bounding box
    # --------------------------------------------------------

    west = lon - radius_deg

    south = lat - radius_deg

    east = lon + radius_deg

    north = lat + radius_deg

    area = (
        f"{west},{south},"
        f"{east},{north}"
    )

    print(
        "Searching:",
        area
    )

    # --------------------------------------------------------
    # Fetch FIRMS
    # --------------------------------------------------------

    try:

        rows = await _fetch_firms_rows(
            area,
            "1"
        )

    except Exception as e:

        print(
            "FIRMS detection error:",
            e
        )

        raise

    print(
        "Hotspots Found:",
        len(rows)
    )

    from modules.forest_fire.routes import (
        serialize
    )

    # ========================================================
    # NO FIRE FOUND
    # ========================================================

    if len(rows) == 0:

        print(
            "No hotspot found."
        )

        now = datetime.now(
            timezone.utc
        )

        safe_event = EventModel(

            disaster_type="forest_fire",

            source="real",

            external_id=(
                "safe_"
                f"{now.timestamp()}"
            ),

            event_time=now,

            lat=lat,

            lon=lon,

            region=(
                f"Lat {lat:.3f}, "
                f"Lon {lon:.3f}"
            ),

            input_data={

                "latitude": lat,

                "longitude": lon,

                "brightness": 0.0,

                "scan": 0.0,

                "track": 0.0,

                "confidence": 0.0,

                "bright_t31": 0.0,

                "daynight_encoded": 0,

                "month": now.month,

                "day_of_year": (
                    now.timetuple().tm_yday
                ),

                "type": 0,

                "status": "SAFE",

                "message": (
                    "No active forest fire detected"
                ),

                "frp": 0.0,

                "raw_confidence": "none",

                "daynight": "N",

                "satellite": "NASA FIRMS",

                "instrument": "VIIRS",

                "ml_prediction": "low",

                "ml_confidence": 1.0,

                "ml_probabilities": {

                    "high": 0.0,

                    "low": 1.0,

                    "medium": 0.0

                }

            },

            risk_score=0.0,

            severity_tier="low",

            fund_status="not_applicable"

        )

        async with async_session() as session:

            session.add(
                safe_event
            )

            await session.commit()

            await session.refresh(
                safe_event
            )

        print(
            "SAFE record inserted."
        )

        return [
            serialize(
                safe_event
            )
        ]

    # ========================================================
    # HOTSPOTS FOUND
    # ========================================================

    inserted = []

    async with async_session() as session:

        for row in rows:

            external_id = (
                _make_external_id(row)
            )

            try:

                # ------------------------------------------------
                # Check existing event
                # ------------------------------------------------

                result = await session.execute(

                    select(
                        EventModel
                    ).where(

                        EventModel.external_id
                        == external_id

                    )

                )

                existing_event = (
                    result.scalar_one_or_none()
                )

                # ------------------------------------------------
                # Existing event
                # ------------------------------------------------

                if existing_event is not None:

                    print(
                        "\nExisting FIRMS hotspot found -> "
                        f"{existing_event.region}"
                    )

                    # IMPORTANT:
                    # Recalculate XGBoost for existing records.

                    if RECALCULATE_EXISTING_ML:

                        print(
                            "Recalculating XGBoost prediction..."
                        )

                        _update_existing_event_with_ml(
                            existing_event,
                            row
                        )

                        await session.commit()

                        await session.refresh(
                            existing_event
                        )

                        print(
                            "UPDATED ML SEVERITY -> "
                            f"{existing_event.severity_tier}"
                        )

                        print(
                            "UPDATED ML CONFIDENCE -> "
                            f"{existing_event.input_data.get('ml_confidence')}"
                        )

                    else:

                        print(
                            "Keeping existing ML result."
                        )

                    inserted.append(
                        existing_event
                    )

                    continue

                # ------------------------------------------------
                # Create new event
                # ------------------------------------------------

                db_row = _build_event_model(
                    row
                )

                session.add(
                    db_row
                )

                await session.commit()

                await session.refresh(
                    db_row
                )

                print(
                    "\nREAL FIRE INSERTED -> "
                    f"{db_row.region}"
                )

                print(
                    "ML SEVERITY -> "
                    f"{db_row.severity_tier}"
                )

                print(
                    "ML CONFIDENCE -> "
                    f"{db_row.input_data.get('ml_confidence')}"
                )

                print(
                    "RISK SCORE -> "
                    f"{db_row.risk_score}"
                )

                inserted.append(
                    db_row
                )

            except IntegrityError:

                await session.rollback()

                print(
                    "Duplicate FIRMS hotspot detected."
                )

                # ------------------------------------------------
                # Retrieve existing event
                # ------------------------------------------------

                result = await session.execute(

                    select(
                        EventModel
                    ).where(

                        EventModel.external_id
                        == external_id

                    )

                )

                existing_event = (
                    result.scalar_one_or_none()
                )

                if existing_event is not None:

                    if RECALCULATE_EXISTING_ML:

                        _update_existing_event_with_ml(
                            existing_event,
                            row
                        )

                        await session.commit()

                        await session.refresh(
                            existing_event
                        )

                    inserted.append(
                        existing_event
                    )

                else:

                    print(
                        "Could not retrieve duplicate event."
                    )

            except Exception as e:

                await session.rollback()

                print(
                    "Error inserting hotspot:",
                    e
                )

    # ========================================================
    # RETURN RESULTS
    # ========================================================

    print(
        "\n=========================================="
    )

    print(
        "FOREST FIRE DETECTION COMPLETE"
    )

    print(
        "Returned records:",
        len(inserted)
    )

    print(
        "=========================================="
    )

    return [

        serialize(x)

        for x in inserted

    ]


# ============================================================
# 11. BACKGROUND FIRMS POLLING
# ============================================================

async def start_polling():

    print(
        "\n=========================================="
    )

    print(
        "FOREST FIRE FIRMS POLLING STARTED"
    )

    print(
        "=========================================="
    )

    print(
        f"Polling interval: "
        f"{POLL_INTERVAL_SECONDS} seconds"
    )

    while True:

        try:

            await fetch_and_process()

        except Exception as e:

            print(
                "Forest Fire Poll Error:",
                e
            )

        await asyncio.sleep(
            POLL_INTERVAL_SECONDS
        )