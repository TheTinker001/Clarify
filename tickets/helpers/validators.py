"""Validator functions."""

from django.core.exceptions import ValidationError


def validate_file_size(file):
    """Raise ValidationError if the uploaded file exceeds 5 MB."""
    max_size_mb = 5
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File size cannot exceed {max_size_mb}MB")
