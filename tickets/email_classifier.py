"""Classify email text into Ticket field values using keyword matching."""

from tickets.email_keywords import (
    FACULTY_KEYWORDS,
    STUDY_LEVEL_KEYWORDS,
    CATEGORY_KEYWORDS,
)


def _match_keywords(text, keyword_map):
    """Return the best matching key from keyword_map, or None."""
    text_lower = text.lower()
    best_match = None
    best_count = 0

    for code, keywords in keyword_map.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_match = code

    return best_match if best_count > 0 else None


def classify_email(subject, body):
    """
    Attempt to classify an email into faculty, study_level, and category.

    Returns a dict with keys 'faculty', 'study_level', 'category'.
    Values are the matched code or None if not detected.
    """
    text = f"{subject} {body}"
    return {
        "faculty": _match_keywords(text, FACULTY_KEYWORDS),
        "study_level": _match_keywords(text, STUDY_LEVEL_KEYWORDS),
        "category": _match_keywords(text, CATEGORY_KEYWORDS),
    }
