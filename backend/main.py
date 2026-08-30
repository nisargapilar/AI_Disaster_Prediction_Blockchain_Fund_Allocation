from fastapi import FastAPI
import asyncio

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CORS MIDDLEWARE
# ============================================================

from fastapi.middleware.cors import CORSMiddleware

# ============================================================
# NOTIFICATION
# ============================================================

from modules.notify.routes import router as notify_router
from modules.notify.digest import digest_loop

# ============================================================
# EARTHQUAKE
# ============================================================
# IMPORTANT:
# Earthquake files are NOT modified.
#
# Earthquake detection is still enabled.
#
# Earthquake routes are NOT imported here because
# earthquake/routes.py imports earthquake/prediction.py,
# which loads the existing Keras model and causes the
# GlorotUniform input_axes compatibility error.
# ============================================================

from modules.earthquake.detection import (
    start_polling as earthquake_start_polling
)

# ============================================================
# FOREST FIRE
# ============================================================

from modules.forest_fire.routes import router as forest_fire_router

from modules.forest_fire.detection import (
    start_polling as forest_fire_start_polling
)

from modules.forest_fire.prediction import (
    start_prediction_polling as forest_fire_prediction_loop
)

# ============================================================
# FLOOD
# ============================================================

from modules.flood.routes import router as flood_router

from modules.flood.detection import (
    start_polling as flood_start_polling
)

from modules.flood.prediction import (
    start_prediction_polling as flood_prediction_loop
)

# ============================================================
# CYCLONE
# ============================================================

from modules.cyclone.routes import router as cyclone_router

from modules.cyclone.detection import (
    start_polling as cyclone_start_polling
)

# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Disaster Prediction and Fund Allocation System"
)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# REGISTER API ROUTES
# ============================================================

app.include_router(notify_router)

# NOTE:
# Earthquake router is intentionally NOT included.
# This prevents earthquake/prediction.py from being loaded.

app.include_router(forest_fire_router)

app.include_router(flood_router)

app.include_router(cyclone_router)

# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup_event():

    print("========================================")
    print("STARTUP EVENT RUNNING")
    print("========================================")

    # --------------------------------------------------------
    # EARTHQUAKE
    # --------------------------------------------------------

    print("Starting Earthquake detection...")

    asyncio.create_task(
        earthquake_start_polling()
    )

    print("Earthquake detection: ENABLED")
    print("Earthquake prediction: SKIPPED")

    # --------------------------------------------------------
    # NOTIFICATION
    # --------------------------------------------------------

    print("Starting Notification service...")

    asyncio.create_task(
        digest_loop()
    )

    # --------------------------------------------------------
    # FLOOD
    # --------------------------------------------------------

    print("Starting Flood detection...")

    asyncio.create_task(
        flood_start_polling()
    )

    print("Starting Flood prediction...")

    asyncio.create_task(
        flood_prediction_loop()
    )

    # --------------------------------------------------------
    # FOREST FIRE
    # --------------------------------------------------------

    print("Starting Forest Fire detection...")

    asyncio.create_task(
        forest_fire_start_polling()
    )

    print("Starting Forest Fire prediction...")

    asyncio.create_task(
        forest_fire_prediction_loop()
    )

    # --------------------------------------------------------
    # CYCLONE
    # --------------------------------------------------------

    print("Starting Cyclone detection...")

    asyncio.create_task(
        cyclone_start_polling()
    )

    # --------------------------------------------------------
    # STARTUP COMPLETE
    # --------------------------------------------------------

    print("========================================")
    print("ALL ENABLED SERVICES STARTED")
    print("========================================")
    print("Earthquake detection : ENABLED")
    print("Earthquake prediction: SKIPPED")
    print("Flood detection      : ENABLED")
    print("Flood prediction     : ENABLED")
    print("Forest Fire          : ENABLED")
    print("Cyclone              : ENABLED")
    print("========================================")


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
async def root():

    return {
        "status": "AI Disaster Prediction and Fund Allocation System backend running",
        "earthquake_detection": "enabled",
        "earthquake_prediction": "temporarily disabled",
        "flood_detection": "enabled",
        "flood_prediction": "enabled",
        "forest_fire": "enabled",
        "cyclone": "enabled"
    }