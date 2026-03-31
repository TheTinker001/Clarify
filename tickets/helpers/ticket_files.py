"""Helper classes for inputting multiple files."""

from django.core.validators import FileExtensionValidator
from django import forms
from django.conf import settings
from tickets.helpers.validators import validate_file_size


class MultipleFileInput(forms.ClearableFileInput):
    """File input widget that allows the user to select more than one file at a time."""

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Form field that validates and returns multiple uploaded files as a list."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        """
        Normalise data to a list and validate each file individually.

        Some parsers pass a bare file object instead of a one-element list when
        only one file is selected.
        Both cases are handled so callers always get a list.
        """
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = []
            for d in data:
                f = single_file_clean(d, initial)
                self._validate_single_file(f)
                result.append(f)
        else:
            result = [single_file_clean(data, initial)]
            self._validate_single_file(result[0])
        return result

    def _validate_single_file(self, f):
        """Run extension and size validators against a single file object."""
        if f:
            ext_validator = FileExtensionValidator(
                allowed_extensions=settings.ALLOWED_EXTENSIONS
            )
            ext_validator(f)
            validate_file_size(f)
