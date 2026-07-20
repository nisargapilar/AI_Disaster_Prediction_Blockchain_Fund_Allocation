# modules/flood/config.py

# Locations to monitor
LOCATIONS = [
    {
        "region": "Assam (Guwahati)",
        "lat": 26.14,
        "lon": 91.74,
    },
    {
        "region": "Patna",
        "lat": 25.59,
        "lon": 85.14,
    },
    {
        "region": "Kochi",
        "lat": 9.93,
        "lon": 76.27,
    },
    {
        "region": "Chennai",
        "lat": 13.08,
        "lon": 80.27,
    },
    {
        "region": "Mumbai",
        "lat": 19.07,
        "lon": 72.88,
    },
]

# Flood severity thresholds
SEVERITY_THRESHOLDS = [
    (0.90, "critical", 0.95),
    (0.70, "high", 0.75),
    (0.40, "medium", 0.50),
    (0.00, "low", 0.20),
]

# Minimum severity eligible for fund allocation
FUND_ELIGIBLE_TIER = "high"

# Poll weather API every 1 hour
POLL_INTERVAL_SECONDS = 3600