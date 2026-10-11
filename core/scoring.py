def calculate_score(correct: int, total: int) -> float:
    """Returns a percentage 0-100."""
    if total == 0:
        return 0.0
    return round((correct / total) * 100, 1)


def grade_label(score: float) -> str:
    """Gives a human-friendly label."""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Strong"
    elif score >= 60:
        return "Average"
    elif score >= 40:
        return "Needs work"
    else:
        return "Weak"


# ---------- IQ SCORING ----------

def calculate_iq_score(domain_scores: dict) -> dict:
    """
    Calculate an IQ-like score from domain percentages.

    domain_scores: dict like {"verbal": 80.0, "numerical": 70.0, "logical": 60.0, "spatial": 90.0}

    Returns a dict with:
      - overall: IQ estimate (mean ~100, std ~15)
      - domains: dict of domain -> IQ estimate
      - label: human-friendly label
    """
    if not domain_scores:
        return {"overall": 0, "domains": {}, "label": "No data"}

    domain_iq = {}
    for domain, pct in domain_scores.items():
        # Map percentage (0-100) to IQ scale (mean 100, std 15)
        # 50% → 100, each 10% → ±15 IQ points
        iq = round(100 + (pct - 50) * 15 / 50)
        domain_iq[domain] = iq

    overall = round(sum(domain_iq.values()) / len(domain_iq))

    if overall >= 130:
        label = "Very Superior"
    elif overall >= 120:
        label = "Superior"
    elif overall >= 110:
        label = "High Average"
    elif overall >= 90:
        label = "Average"
    elif overall >= 80:
        label = "Low Average"
    elif overall >= 70:
        label = "Borderline"
    else:
        label = "Below Average"

    return {
        "overall": overall,
        "domains": domain_iq,
        "label": label,
    }


# ---------- EQ SCORING ----------

def calculate_eq_score(correct: int, total: int) -> dict:
    """
    Calculate an EQ score from correct/total answers.

    Returns a dict with:
      - score: percentage 0-100
      - level: EQ level label
      - description: brief description
    """
    if total == 0:
        return {"score": 0, "level": "No data", "description": ""}

    score = round((correct / total) * 100, 1)

    if score >= 90:
        level = "Very High EQ"
        description = "You show exceptional emotional awareness and social skills."
    elif score >= 75:
        level = "High EQ"
        description = "You handle emotions well and relate effectively to others."
    elif score >= 60:
        level = "Moderate EQ"
        description = "You have decent emotional skills with room for growth."
    elif score >= 40:
        level = "Developing EQ"
        description = "You could benefit from practicing empathy and self-regulation."
    else:
        level = "Low EQ"
        description = "Working on emotional awareness would greatly help your relationships."

    return {
        "score": score,
        "level": level,
        "description": description,
    }