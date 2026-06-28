import re
import math

def get_stylometric_score(text: str) -> float:
    """
    Analyzes structural/statistical properties of text to estimate
    likelihood of AI generation. Returns float between 0.0 and 1.0.
    1.0 = likely AI, 0.0 = likely human.
    """

    sentences = _split_sentences(text)
    words = _get_words(text)

    if len(sentences) < 2 or len(words) < 10:
        return 0.5  # Not enough data, return uncertain

    # Metric 1: Sentence length variance
    # AI writing tends to have low variance (uniform sentence lengths)
    sentence_lengths = [len(_get_words(s)) for s in sentences]
    variance = _variance(sentence_lengths)
    # Low variance → high AI likelihood
    # Normalize: variance of 0 = 1.0 (AI), variance of 50+ = 0.0 (human)
    variance_score = max(0.0, 1.0 - (variance / 50.0))

    # Metric 2: Type-token ratio (vocabulary diversity)
    # Lower ratio = more repetition = more likely human casual writing
    # Higher ratio = more diverse vocab = could be AI or formal human
    unique_words = set(w.lower() for w in words)
    ttr = len(unique_words) / len(words)
    # High TTR → higher AI likelihood
    ttr_score = min(1.0, ttr * 1.5)

    # Metric 3: Punctuation density
    # AI tends to use punctuation consistently and moderately
    punct_count = len(re.findall(r'[,;:—\-]', text))
    punct_density = punct_count / len(words)
    # Normalize: moderate punctuation (0.1-0.2) = more AI-like
    punct_score = min(1.0, punct_density * 5.0)

    # Combine three metrics equally
    final_score = (variance_score * 0.5) + (ttr_score * 0.3) + (punct_score * 0.2)

    return round(max(0.0, min(1.0, final_score)), 4)


def _split_sentences(text: str) -> list:
    """Split text into sentences."""
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]

def _get_words(text: str) -> list:
    """Extract words from text."""
    return re.findall(r'\b[a-zA-Z]+\b', text)

def _variance(values: list) -> float:
    """Calculate variance of a list of numbers."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / len(values)