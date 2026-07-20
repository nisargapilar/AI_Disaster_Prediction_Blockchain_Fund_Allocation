import os
from dotenv import load_dotenv

load_dotenv()


# OpenWeather API details
WEATHER_API_URL = os.getenv("WEATHER_API_URL")

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


# Cyclone severity thresholds
# score -> tier -> fund priority

SEVERITY_THRESHOLDS = [
    (80, "critical", 0.95),
    (50, "high", 0.75),
    (30, "medium", 0.5),
    (0, "low", 0.2),
]


# Minimum tier eligible for fund allocation
FUND_ELIGIBLE_TIER = "high"


# Automatic update interval
# 60 seconds × 60 minutes = 3600 seconds
POLL_INTERVAL_SECONDS = 3600