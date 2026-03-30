"""Tests for the ticket detail response."""

from django.test import TestCase, override_settings
from unittest.mock import patch
from tickets.tests.helpers import MenuTesterMixin
from tickets.models import User, Ticket, Comment


@override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=0)
class TicketDetailCommentEmailTestCase(TestCase, MenuTesterMixin):
    """Test suite for the ticket detail response."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.student2 = User.objects.get(username="@petrapickles")
        self.staff = User.objects.get(username="@janedoe")
        self.staff.user_type = User.USER_TYPE_STAFF
        self.staff.save()
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Update card access",
            body="Card access not working for lab.",
        )
        self.ticket.assigned_to.add(self.staff)
        self.url = self.ticket.get_absolute_url()

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
        SITE_URL="http://testserver",
    )
    def test_email_sent_to_student_when_staff_responds(self):
        self.client.login(username=self.staff.username, password="Password123")
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            self.client.post(
                self.url,
                {"action": "add_comment", "body": "Here is your answer.."},
                follow=True,
            )
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            self.assertIn(self.student.email, call_kwargs["recipient_list"])
            self.assertIn("Update card access", call_kwargs["subject"])
            self.assertIn(self.ticket.url_code, call_kwargs["message"])
            self.assertIn("Here is your answer.", call_kwargs["message"])

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_no_email_sent_when_student_responds(self):
        self.ticket.status = Ticket.Status.AWAITING_STUDENT
        self.ticket.save()
        self.client.login(username=self.student.username, password="Password123")
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            self.client.post(self.url, {"body": "Follow-up."})
            mock_send.assert_not_called()

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_ticket_still_saved_when_email_fails(self):
        self.client.login(username=self.staff.username, password="Password123")
        with patch(
            "tickets.helpers.email.email_notifications.send_mail",
            side_effect=Exception("SMTP fail"),
        ):
            resp = self.client.post(
                self.url, {"action": "add_comment", "body": "Answer."}, follow=True
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)

    def test_no_email_sent_without_email_settings(self):
        self.client.login(username=self.staff.username, password="Password123")
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            self.client.post(self.url, {"body": "Answer."})
            mock_send.assert_not_called()

    def test_responses_context_is_passed(self):
        Comment.objects.create(
            ticket=self.ticket, author=self.staff, body="First response."
        )
        Comment.objects.create(
            ticket=self.ticket, author=self.student, body="Student follow-up."
        )
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["comments"]), 2)
