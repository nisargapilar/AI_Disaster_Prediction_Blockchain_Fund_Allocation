SEVERITY_THRESHOLDS = [
    (7.0, "critical", 0.95),
    (5.5, "high", 0.75),
    (4.0, "medium", 0.5),
    (0.0, "low", 0.2),
]
FUND_ELIGIBLE_TIER = "high"
USGS_FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
POLL_INTERVAL_SECONDS = 30