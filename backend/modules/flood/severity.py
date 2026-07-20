from modules.flood.config import (
    SEVERITY_THRESHOLDS,
    FUND_ELIGIBLE_TIER,
)

TIER_ORDER = [
    "low",
    "medium",
    "high",
    "critical",
]


def compute_severity(probability: float):
    """
    Determine severity tier and risk score
    from the calculated flood probability.
    """

    probability = max(0.0, min(probability, 1.0))

    for minimum, tier, score in SEVERITY_THRESHOLDS:
        if probability >= minimum:
            return tier, score

    # Default fallback
    return "low", 0.20


def is_fund_eligible(tier: str):
    """
    Returns True if the severity is eligible
    for fund allocation.
    """

    if tier not in TIER_ORDER:
        return False

    return (
        TIER_ORDER.index(tier)
        >= TIER_ORDER.index(FUND_ELIGIBLE_TIER)
    )