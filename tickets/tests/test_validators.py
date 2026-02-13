from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from tickets.helpers import _validate_file_size


class ValidateFileSizeTest(TestCase):
    """Tests for the _validate_file_size validator."""

    def test_accepts_file_within_size_limit(self):
        small_content = b"x" * (1 * 1024 * 1024)
        file = SimpleUploadedFile("small.pdf", small_content)

        try:
            _validate_file_size(file)
        except ValidationError:
            self.fail("_validate_file_size raised ValidationError for valid file size")

    def test_accepts_file_at_exact_limit(self):
        exact_content = b"x" * (5 * 1024 * 1024)
        file = SimpleUploadedFile("exact.pdf", exact_content)

        try:
            _validate_file_size(file)
        except ValidationError:
            self.fail("_validate_file_size raised ValidationError for 5MB file")

    def test_rejects_file_over_size_limit(self):
        large_content = b"x" * (6 * 1024 * 1024)
        file = SimpleUploadedFile("large.pdf", large_content)

        with self.assertRaises(ValidationError) as context:
            _validate_file_size(file)

        self.assertIn("5MB", str(context.exception))

    def test_error_message_is_clear(self):
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        file = SimpleUploadedFile("toolarge.pdf", large_content)

        with self.assertRaises(ValidationError) as context:
            _validate_file_size(file)

        error_message = str(context.exception)
        self.assertIn("File size cannot exceed 5MB", error_message)
