from modules.cyclone.config import (
    SEVERITY_THRESHOLDS,
    FUND_ELIGIBLE_TIER
)


def compute_severity(wind_speed, pressure):

    score = 0

    # Wind speed calculation
    if wind_speed >= 120:
        score += 50

    elif wind_speed >= 80:
        score += 30


    # Pressure calculation
    if pressure <= 980:
        score += 50

    elif pressure <= 1000:
        score += 30


    # Find severity tier
    for threshold, tier, confidence in SEVERITY_THRESHOLDS:

        if score >= threshold:
            return tier, score


    return "low", score



def is_fund_eligible(tier):

    severity_order = [
        "low",
        "medium",
        "high",
        "critical"
    ]

    return (
        severity_order.index(tier)
        >= severity_order.index(FUND_ELIGIBLE_TIER)
    )