import os
from dotenv import load_dotenv

load_dotenv()

SEVERITY_THRESHOLDS = [
    (7.0, "critical", 0.95),
    (5.5, "high", 0.75),
    (4.0, "medium", 0.5),
    (0.0, "low", 0.2),
]
FUND_ELIGIBLE_TIER = "high"
USGS_FEED_URL = os.getenv("USGS_FEED_URL")
POLL_INTERVAL_SECONDS = 30