def get_confidence_score(groq_score: float, stylometric_score: float) -> float:
    """
    Combines two signal scores into a single confidence score.
    Weights: Groq 0.6, Stylometric 0.4 (as defined in planning.md)
    Returns float between 0.0 and 1.0.
    """
    combined = (groq_score * 0.6) + (stylometric_score * 0.4)
    return round(max(0.0, min(1.0, combined)), 4)