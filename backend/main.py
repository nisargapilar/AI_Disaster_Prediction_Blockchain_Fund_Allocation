from fastapi import FastAPI
import asyncio

from modules.earthquake.routes import router as earthquake_router
from modules.earthquake.detection import start_polling as earthquake_start_polling

app = FastAPI(title=" AI Disaster Prediction and Fund Allocation System")

app.include_router(earthquake_router)

@app.on_event("startup")
async def startup():
    asyncio.create_task(earthquake_start_polling())

@app.get("/")
async def root():
    return {"status": " AI Disaster Prediction and Fund Allocation System backend running"}