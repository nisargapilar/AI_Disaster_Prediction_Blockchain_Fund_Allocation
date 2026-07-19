from modules.earthquake.config import SEVERITY_THRESHOLDS, FUND_ELIGIBLE_TIER

TIER_ORDER = ["low", "medium", "high", "critical"]

def compute_severity(magnitude: float):
    for min_mag, tier, score in SEVERITY_THRESHOLDS:
        if magnitude >= min_mag:
            return tier, score
    return "low", 0.1

def is_fund_eligible(tier: str) -> bool:
    return TIER_ORDER.index(tier) >= TIER_ORDER.index(FUND_ELIGIBLE_TIER)