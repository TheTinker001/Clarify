"""Tests for conditional email helper: send_reminder_email"""

from django.test import TestCase, override_settings
from unittest.mock import patch
from tickets.helpers.email.email_notifications import send_reminder_email
from tickets.models import Ticket
from clarify.settings import INACTIVE_TICKET_FIRST_REMINDER
from django.contrib.auth import get_user_model

User = get_user_model()


class SendReminderEmailTest(TestCase):
    """Tests for conditional email helper: send_reminder_email"""

    def setUp(self):
        self.student = User.objects.create_user(
            username="@remindstudent",
            email="remind@test.com",
            password="Password123",
            first_name="Remind",
            last_name="Me",
            user_type="student",
        )
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Need help",
            body="Body.",
        )

    @override_settings(EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD="")
    def test_no_email_when_no_credentials(self):
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_reminder_email(self.ticket)
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
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_reminder_email(self.ticket)
            mock_send.assert_not_called()

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
    def test_reminder_email_sent(self):
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_reminder_email(self.ticket)
            mock_send.assert_called_once()
            kw = mock_send.call_args.kwargs
            self.assertIn("remind@test.com", kw["recipient_list"])
            self.assertIn("Reminder", kw["subject"])
            self.assertIn("Need help", kw["subject"])
            self.assertIn(self.ticket.url_code, kw["message"])
            self.assertIn(str(INACTIVE_TICKET_FIRST_REMINDER), kw["message"])
