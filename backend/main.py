from fastapi import FastAPI
import asyncio

# ============================================================
# LOAD ENVIRONMENT VARIABLES FIRST
# ============================================================

from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CORS MIDDLEWARE (for frontend connection)
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite's dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# REGISTER API ROUTES
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

    print("STARTUP EVENT RUNNING")

    # Earthquake
    asyncio.create_task(
        earthquake_start_polling()
    )

    asyncio.create_task(
        earthquake_prediction_loop()
    )

    # Notification daily digest
    asyncio.create_task(
        digest_loop()
    )

    # Flood
    asyncio.create_task(
        flood_start_polling()
    )

    # Forest Fire
    asyncio.create_task(
        forest_fire_start_polling()
    )

    asyncio.create_task(
        forest_fire_prediction_loop()
    )

    # Cyclone
    asyncio.create_task(
        cyclone_start_polling()
    )


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
async def root():

    return {
        "status":
        "AI Disaster Prediction and Fund Allocation System backend running"
    }