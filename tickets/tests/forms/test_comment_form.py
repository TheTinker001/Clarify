"""Tests for the CommentForm."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from tickets.forms import CommentForm
from tickets.models import Comment


class CommentFormTestCase(TestCase):
    """Test suite for the CommentForm."""

    def test_valid_form(self):
        form = CommentForm(data={"body": "A valid comment."})
        self.assertTrue(form.is_valid())

    def test_blank_body_is_invalid(self):
        form = CommentForm(data={"body": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("body", form.errors)

    def test_body_too_long_is_invalid(self):
        form = CommentForm(data={"body": "a" * (Comment.BODY_MAX_LENGTH + 1)})
        self.assertFalse(form.is_valid())
        self.assertIn("body", form.errors)

    def test_body_at_max_length_is_valid(self):
        form = CommentForm(data={"body": "a" * Comment.BODY_MAX_LENGTH})
        self.assertTrue(form.is_valid())

    def test_attachments_field_is_optional(self):
        form = CommentForm()
        self.assertFalse(form.fields["attachments"].required)

    def test_attachments_accepts_valid_file(self):
        file = SimpleUploadedFile(
            "test.pdf", b"file content", content_type="application/pdf"
        )
        form = CommentForm(data={"body": "A comment."}, files={"attachments": file})
        self.assertTrue(form.is_valid())

    def test_attachments_rejects_invalid_file_type(self):
        file = SimpleUploadedFile(
            "test.exe", b"file content", content_type="application/exe"
        )
        form = CommentForm(data={"body": "A comment."}, files={"attachments": file})
        self.assertFalse(form.is_valid())
        self.assertIn("attachments", form.errors)

    def test_attachments_rejects_large_file(self):
        file = SimpleUploadedFile(
            "large.pdf", b"x" * (6 * 1024 * 1024), content_type="application/pdf"
        )
        form = CommentForm(data={"body": "A comment."}, files={"attachments": file})
        self.assertFalse(form.is_valid())
        self.assertIn("attachments", form.errors)
