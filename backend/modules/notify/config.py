# modules/notify/config.py

import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
DAILY_DIGEST_HOUR_UTC = 6  # for later — digest sends at 06:00 UTC