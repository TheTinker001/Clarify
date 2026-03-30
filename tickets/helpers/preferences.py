"""Staff preferences helper functions."""


def split_codes(value):
    """Split a comma-separated preference string into a stripped, non-empty list."""
    return [c.strip() for c in value.split(",") if c.strip()]
