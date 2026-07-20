from fastapi import FastAPI
import asyncio

# Earthquake
from modules.earthquake.routes import router as earthquake_router
from modules.earthquake.detection import start_polling as earthquake_start_polling

# Flood
from modules.flood.routes import router as flood_router
from modules.flood.detection import start_polling as flood_start_polling

# Cyclone
from modules.cyclone.routes import router as cyclone_router
from modules.cyclone.detection import start_polling as cyclone_start_polling

app = FastAPI(
    title="AI Disaster Prediction and Fund Allocation System"
)

# Register API routes
app.include_router(earthquake_router)
app.include_router(flood_router)
app.include_router(cyclone_router)


@app.on_event("startup")
async def startup_event():
    print("STARTUP EVENT RUNNING")

    asyncio.create_task(earthquake_start_polling())
    asyncio.create_task(flood_start_polling())
    asyncio.create_task(cyclone_start_polling())


@app.get("/")
async def root():
    return {
        "status": "AI Disaster Prediction and Fund Allocation System backend running"
    }