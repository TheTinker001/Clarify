"""Tests for the Comment model."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from tickets.models import Comment, Ticket, User


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
            assigned_to=self.staff,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test subject",
            body="Test body.",
        )
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

    def test_comment_body_too_long(self):
        long_body = "a" * (Comment.BODY_MAX_LENGTH + 1)
        comment = Comment(
            ticket=self.ticket,
            author=self.student,
            body=long_body,
        )
        with self.assertRaises(ValidationError):
            comment.full_clean()

    def test_comment_body_at_max_length(self):
        body = "a" * Comment.BODY_MAX_LENGTH
        comment = Comment(
            ticket=self.ticket,
            author=self.student,
            body=body,
        )
        comment.full_clean()
