"""Tests for the Comment model."""

from django.test import TestCase
from tickets.models import Comment, Ticket, User
from unittest.mock import patch


class CommentModelTestCase(TestCase):
    """Test suite for the Comment model."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.get(username="@janedoe")
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test subject",
            body="Test body.",
        )
        self.ticket.assigned_to.add(self.staff)
        self.comment = Comment.objects.create(
            ticket=self.ticket,
            author=self.student,
            body="This is a test comment.",
        )

    def test_comment_creation(self):
        self.assertEqual(self.comment.ticket, self.ticket)
        self.assertEqual(self.comment.author, self.student)
        self.assertEqual(self.comment.body, "This is a test comment.")
        self.assertIsNotNone(self.comment.created_at)

    def test_comment_str(self):
        expected = f"Comment by {self.student} on Ticket {self.ticket.pk}"
        self.assertEqual(str(self.comment), expected)

    def test_comment_ordering(self):
        comment2 = Comment.objects.create(
            ticket=self.ticket,
            author=self.staff,
            body="Second comment.",
        )
        comments = list(Comment.objects.filter(ticket=self.ticket))
        self.assertEqual(comments[0], self.comment)
        self.assertEqual(comments[1], comment2)

    # Tests for generate_unique_url_code(self)
    def test_generate_unique_url_code_returns_non_empty_string(self):
        code = self.comment.generate_unique_url_code()
        self.assertTrue(isinstance(code, str))
        self.assertTrue(len(code) == 10)

    def test_generate_unique_url_code_retries_on_collision(self):
        """Method must retry when token_urlsafe generates a duplicate."""
        comment2 = Comment.objects.create(
            ticket=self.ticket,
            author=self.student,
            body="This is a second test comment.",
            url_code="collisi",
        )

        # First call produces a collision, second call produces unique result
        with patch(
            "tickets.models.ticket.secrets.token_urlsafe",
            side_effect=["collisi", "unique4"],
        ):
            code = comment2.generate_unique_url_code()

        self.assertEqual(code, "unique4")
