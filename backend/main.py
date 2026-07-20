from fastapi import FastAPI
import asyncio

from modules.earthquake.routes import router as earthquake_router
from modules.earthquake.detection import start_polling as earthquake_start_polling

from modules.cyclone.routes import router as cyclone_router
from modules.cyclone.detection import start_polling as cyclone_start_polling


app = FastAPI(
    title="AI Disaster Prediction and Fund Allocation System"
)


# Register API routes
app.include_router(earthquake_router)
app.include_router(cyclone_router)


# Start background detection services
@app.on_event("startup")
async def startup():

    print("STARTUP EVENT RUNNING")

    asyncio.create_task(
        earthquake_start_polling()
    )

    asyncio.create_task(
        cyclone_start_polling()
    )


@app.get("/")
async def root():
    return {
        "status": "AI Disaster Prediction and Fund Allocation System backend running"
    }