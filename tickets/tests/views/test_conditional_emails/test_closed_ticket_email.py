"""Tests for conditional email helper: _send_ticket_closed_email"""

from django.test import TestCase, override_settings
from unittest.mock import patch
from tickets.conditional_emails import _send_ticket_closed_email
from tickets.models import Ticket
from django.contrib.auth import get_user_model

User = get_user_model()


class SendClosedTicketEmailTest(TestCase):
    """Tests for conditional email helper: _send_ticket_closed_email"""

    def setUp(self):
        self.student = User.objects.create_user(
            username="@closestudent",
            email="close@test.com",
            password="Password123",
            first_name="Close",
            last_name="Me",
            user_type="student",
        )
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="My query",
            body="Body.",
        )

    @override_settings(EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD="")
    def test_no_email_when_no_credentials(self):
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            _send_ticket_closed_email(self.ticket, "answered")
            mock_send.assert_not_called()

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
    def test_no_email_when_student_has_no_email(self):
        self.student.email = ""
        self.student.save()
        self.ticket.refresh_from_db()
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            _send_ticket_closed_email(self.ticket, "answered")
            mock_send.assert_not_called()

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
    def test_closed_answered_email(self):
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            _send_ticket_closed_email(self.ticket, "answered")
            mock_send.assert_called_once()
            kw = mock_send.call_args.kwargs
            self.assertIn("close@test.com", kw["recipient_list"])
            self.assertIn("closed", kw["subject"].lower())
            self.assertIn("answered", kw["message"].lower())

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
    def test_closed_inactivity_email(self):
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            _send_ticket_closed_email(self.ticket, "inactivity")
            mock_send.assert_called_once()
            kw = mock_send.call_args.kwargs
            self.assertIn("inactivity", kw["message"].lower())

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="",
        SITE_URL="http://testserver",
    )
    def test_falls_back_to_host_user_when_no_default_from(self):
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            _send_ticket_closed_email(self.ticket, "answered")
            self.assertEqual(mock_send.call_args.kwargs["from_email"], "c@e.com")
