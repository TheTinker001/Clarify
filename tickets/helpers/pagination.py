"""Pagination helper functions."""

from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django import forms
from django.conf import settings


def get_page_slots(cur, max_pages):
    if max_pages <= 9:
        return list(range(1, max_pages + 1))
    slots = []
    if cur <= 4:
        slots = list(range(1, 8)) + ["...", max_pages]
    elif cur >= max_pages - 3:
        slots = [1, "..."] + list(range(max_pages - 6, max_pages + 1))
    else:
        slots = [1, "..."] + list(range(cur - 2, cur + 3)) + ["...", max_pages]
    return slots
