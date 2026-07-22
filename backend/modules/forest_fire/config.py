import os
from dotenv import load_dotenv

load_dotenv()
print("FIRMS_MAP_KEY =", os.getenv("FIRMS_MAP_KEY"))

# NASA FIRMS satellite hotspot feed (free, requires registration for a MAP_KEY)
# Register at: https://firms.modaps.eosdis.nasa.gov/api/map_key/
FIRMS_MAP_KEY = os.getenv("FIRMS_MAP_KEY")
FIRMS_SOURCE = os.getenv("FIRMS_SOURCE", "VIIRS_SNPP_NRT")
FIRMS_AREA = os.getenv("FIRMS_AREA", "68,6,98,36")  # default: rough India bbox
FIRMS_DAY_RANGE = os.getenv("FIRMS_DAY_RANGE", "1")
FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

POLL_INTERVAL_SECONDS = int(os.getenv("FIRMS_POLL_INTERVAL_SECONDS", "300"))

# Severity thresholds for CONFIRMED fire detections. FIRMS gives two real
# signals per detection -- confidence and FRP (fire radiative power, how
# intense the fire is) -- which severity.py combines into one score
# (0.6*confidence + 0.4*frp), then maps to a tier here, same fixed-threshold
# style as the earthquake module's magnitude bands.
SEVERITY_THRESHOLDS = [
    (0.80, "critical", 0.90),
    (0.55, "high", 0.65),
    (0.30, "medium", 0.40),
    (0.0, "low", 0.15),
]
FUND_ELIGIBLE_TIER = "high"