import os
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------
# OpenWeather API Configuration
# --------------------------------------------------

WEATHER_API_URL = os.getenv("WEATHER_API_URL")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


# --------------------------------------------------
# High-Risk Cyclone Monitoring Locations
# --------------------------------------------------

CYCLONE_MONITOR_LOCATIONS = [
    {
        "state": "Odisha",
        "region": "Paradip",
        "lat": 20.3167,
        "lon": 86.6167
    },
    {
        "state": "Andhra Pradesh",
        "region": "Visakhapatnam",
        "lat": 17.6868,
        "lon": 83.2185
    },
    {
        "state": "West Bengal",
        "region": "Digha",
        "lat": 21.6265,
        "lon": 87.5084
    },
    {
        "state": "Tamil Nadu",
        "region": "Nagapattinam",
        "lat": 10.7667,
        "lon": 79.8333
    },
    {
        "state": "Gujarat",
        "region": "Kandla",
        "lat": 23.0333,
        "lon": 70.2167
    }
]


# --------------------------------------------------
# Cyclone Severity Thresholds
# (Risk Score -> Severity Tier -> Confidence)
# --------------------------------------------------

SEVERITY_THRESHOLDS = [
    (80, "critical", 0.95),
    (50, "high", 0.75),
    (30, "medium", 0.50),
    (0, "low", 0.20),
]


# --------------------------------------------------
# Minimum Severity Eligible for Fund Allocation
# --------------------------------------------------

FUND_ELIGIBLE_TIER = "high"


# --------------------------------------------------
# Automatic Polling Interval
# 3600 seconds = 1 hour
# --------------------------------------------------

POLL_INTERVAL_SECONDS = 60