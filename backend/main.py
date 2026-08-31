from fastapi import FastAPI
import asyncio
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# ============================================================
# NOTIFICATION
# ============================================================

from modules.notify.routes import router as notify_router
from modules.notify.digest import digest_loop

# ============================================================
# EARTHQUAKE - LEADER PART
# ============================================================

from modules.earthquake.routes import router as earthquake_router
from modules.earthquake.detection import (
    start_polling as earthquake_start_polling
)
from modules.earthquake.prediction import (
    prediction_loop as earthquake_prediction_loop
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
# CYCLONE - YOUR PART
# ============================================================

from modules.cyclone.routes import router as cyclone_router
from modules.cyclone.detection import (
    start_polling as cyclone_start_polling
)
from modules.cyclone.prediction import (
    start_prediction_polling as cyclone_prediction_loop
)

# ============================================================
# FASTAPI
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
# ROUTES
# ============================================================

app.include_router(notify_router)
app.include_router(earthquake_router)
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

    # EARTHQUAKE
    print("Starting Earthquake detection...")
    asyncio.create_task(
        earthquake_start_polling()
    )
    print("Earthquake detection: ENABLED")

    print("Starting Earthquake prediction...")
    asyncio.create_task(
        earthquake_prediction_loop()
    )
    print("Earthquake prediction: ENABLED")

    # NOTIFICATION
    print("Starting Notification service...")
    asyncio.create_task(
        digest_loop()
    )
    print("Notification service: ENABLED")

    # FLOOD
    print("Starting Flood detection...")
    asyncio.create_task(
        flood_start_polling()
    )
    print("Flood detection: ENABLED")

    print("Starting Flood prediction...")
    asyncio.create_task(
        flood_prediction_loop()
    )
    print("Flood prediction: ENABLED")

    # FOREST FIRE
    print("Starting Forest Fire detection...")
    asyncio.create_task(
        forest_fire_start_polling()
    )
    print("Forest Fire detection: ENABLED")

    print("Starting Forest Fire prediction...")
    asyncio.create_task(
        forest_fire_prediction_loop()
    )
    print("Forest Fire prediction: ENABLED")

    # CYCLONE
    print("Starting Cyclone detection...")
    asyncio.create_task(
        cyclone_start_polling()
    )
    print("Cyclone detection: ENABLED")

    print("Starting Cyclone prediction...")
    asyncio.create_task(
        cyclone_prediction_loop()
    )
    print("Cyclone prediction: ENABLED")

    # COMPLETE
    print("========================================")
    print("ALL SERVICES STARTED")
    print("========================================")


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "status": "AI Disaster Prediction and Fund Allocation System backend running",
        "earthquake_detection": "enabled",
        "earthquake_prediction": "enabled",
        "flood_detection": "enabled",
        "flood_prediction": "enabled",
        "forest_fire_detection": "enabled",
        "forest_fire_prediction": "enabled",
        "cyclone_detection": "enabled",
        "cyclone_prediction": "enabled",
        "notification": "enabled"
    }