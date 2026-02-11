"""Tests for the CommentForm."""

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
