"""Tests for the Edit Comment feature."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from tickets.models import Comment, Ticket, User
from clarify.settings import EDIT_TIME_LIMIT_MINUTES


class EditCommentViewTestCase(TestCase):
    """Test suite for editing comments."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.other_student = User.objects.get(username="@petrapickles")
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
            body="Original body text.",
        )
        self.url = self.comment.get_absolute_url()

    # Edit button / form is rendered
    def test_get_renders_edit_form(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_comment.html")

    def test_get_prepopulates_form_with_existing_body(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "Original body text.")

    # Successful edit within time limit
    def test_author_can_edit_within_10_minutes(self):
        self.client.login(username=self.student.username, password="Password123")
        self.client.post(self.url, {"body": "Updated body text."})
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, "Updated body text.")

    def test_edit_redirects_to_ticket_detail(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(self.url, {"body": "Updated."})
        expected_url = reverse(
            "ticket_detail", kwargs={"url_code": self.ticket.url_code}
        )
        self.assertRedirects(response, expected_url)

    # Success notification message
    def test_edit_shows_success_message(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(self.url, {"body": "Updated."}, follow=True)
        self.assertContains(response, "Your message has been edited.")

    # Time limit enforcement
    def test_author_cannot_edit_after_10_minutes(self):
        self.client.login(username=self.student.username, password="Password123")
        future_time = self.comment.created_at + timedelta(minutes=11)
        with patch("tickets.views.edit_comment_view.timezone") as mock_tz:
            mock_tz.now.return_value = future_time
            response = self.client.post(self.url, {"body": "Too late."})
        self.assertEqual(response.status_code, 404)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, "Original body text.")

    def test_boundary_exactly_10_minutes_is_allowed(self):
        self.client.login(username=self.student.username, password="Password123")
        exact_boundary = self.comment.created_at + timedelta(
            minutes=EDIT_TIME_LIMIT_MINUTES
        )
        with patch("tickets.views.edit_comment_view.timezone") as mock_tz:
            mock_tz.now.return_value = exact_boundary
            response = self.client.post(self.url, {"body": "Boundary edit."})
        self.assertEqual(response.status_code, 302)

    # Access control
    def test_non_author_cannot_edit(self):
        self.client.login(username=self.other_student.username, password="Password123")
        response = self.client.post(self.url, {"body": "Sneaky edit."})
        self.assertEqual(response.status_code, 404)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, "Original body text.")

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.post(self.url, {"body": "Anonymous edit."})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/log_in/", response["Location"])

    def test_invalid_body_rerenders_form(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(self.url, {"body": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_comment.html")
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, "Original body text.")
