from modules.forest_fire.config import SEVERITY_THRESHOLDS, FUND_ELIGIBLE_TIER

TIER_ORDER = ["low", "medium", "high", "critical"]


def _confidence_to_score(raw_confidence) -> float:
    """VIIRS confidence is a string (low/nominal/high); MODIS is 0-100."""
    if isinstance(raw_confidence, str):
        mapping = {"low": 0.3, "nominal": 0.6, "high": 0.9}
        return mapping.get(raw_confidence.strip().lower(), 0.5)
    try:
        return max(0.0, min(1.0, float(raw_confidence) / 100.0))
    except (TypeError, ValueError):
        return 0.5


def _frp_to_score(frp) -> float:
    """Fire Radiative Power (MW) -- higher means a more intense fire."""
    try:
        frp = float(frp)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, frp / 100.0))


def compute_severity(confidence_raw, frp: float):
    """
    Mirrors the earthquake module's compute_severity(magnitude) shape.
    Fire detections carry two raw signals (confidence + FRP) instead of
    one, so we combine them into a single score first, then map to a
    tier using the same fixed-threshold approach.
    """
    confidence_score = _confidence_to_score(confidence_raw)
    frp_score = _frp_to_score(frp)
    combined_score = round(0.6 * confidence_score + 0.4 * frp_score, 4)

    for min_score, tier, _ in SEVERITY_THRESHOLDS:
        if combined_score >= min_score:
            return tier, combined_score
    return "low", combined_score


def is_fund_eligible(tier: str) -> bool:
    return TIER_ORDER.index(tier) >= TIER_ORDER.index(FUND_ELIGIBLE_TIER)