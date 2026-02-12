"""Unit tests for the helpers module."""
from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from tickets.models import Ticket
from tickets.helpers import _send_ticket_created_email

User = get_user_model()


class SendTicketCreatedEmailTest(TestCase):
    """Tests for the _send_ticket_created_email helper function."""

    def setUp(self):
        self.student = User.objects.create_user(
            username="@teststudent",
            email="student@test.com",
            password="Password123",
            first_name="Test",
            last_name="Student",
            user_type="student",
        )
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="health_and_wellbeing",
            subject="Test ticket",
            body="Test body content.",
        )

    @override_settings(EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD="")
    def test_no_email_sent_when_email_host_user_is_empty(self):
        """Email is not sent when EMAIL_HOST_USER is empty."""
        with patch("tickets.helpers.send_mail") as mock_send:
            _send_ticket_created_email(self.ticket)
            mock_send.assert_not_called()

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="",
    )
    def test_no_email_sent_when_email_host_password_is_empty(self):
        """Email is not sent when EMAIL_HOST_PASSWORD is empty."""
        with patch("tickets.helpers.send_mail") as mock_send:
            _send_ticket_created_email(self.ticket)
            mock_send.assert_not_called()

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_no_email_sent_when_student_has_no_email(self):
        """Email is not sent when the student has no email address."""
        self.student.email = ""
        self.student.save()
        self.ticket.refresh_from_db()
        with patch("tickets.helpers.send_mail") as mock_send:
            _send_ticket_created_email(self.ticket)
            mock_send.assert_not_called()

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_email_sent_with_correct_subject(self):
        """Email is sent with the correct subject line."""
        with patch("tickets.helpers.send_mail") as mock_send:
            _send_ticket_created_email(self.ticket)
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            self.assertIn(str(self.ticket.pk), call_kwargs["subject"])
            self.assertIn("We received your query", call_kwargs["subject"])

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_email_sent_with_correct_body(self):
        """Email body contains ticket details and student name."""
        with patch("tickets.helpers.send_mail") as mock_send:
            _send_ticket_created_email(self.ticket)
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            body = call_kwargs["message"]
            self.assertIn("Test", body)
            self.assertIn(str(self.ticket.pk), body)
            self.assertIn("Test ticket", body)

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_email_sent_to_student_email(self):
        """Email is sent to the student's email address."""
        with patch("tickets.helpers.send_mail") as mock_send:
            _send_ticket_created_email(self.ticket)
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            self.assertEqual(call_kwargs["recipient_list"], ["student@test.com"])

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_email_sent_from_default_from_email(self):
        """Email is sent from the DEFAULT_FROM_EMAIL address."""
        with patch("tickets.helpers.send_mail") as mock_send:
            _send_ticket_created_email(self.ticket)
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            self.assertEqual(call_kwargs["from_email"], "clarify@example.com")

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="",
    )
    def test_email_falls_back_to_host_user_when_no_default_from(self):
        """Email uses EMAIL_HOST_USER when DEFAULT_FROM_EMAIL is empty."""
        with patch("tickets.helpers.send_mail") as mock_send:
            _send_ticket_created_email(self.ticket)
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            self.assertEqual(call_kwargs["from_email"], "clarify@example.com")

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_email_body_uses_there_when_no_first_name(self):
        """Email body uses 'there' when student has no first name."""
        self.student.first_name = ""
        self.student.save()
        with patch("tickets.helpers.send_mail") as mock_send:
            _send_ticket_created_email(self.ticket)
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            body = call_kwargs["message"]
            self.assertIn("Hi there", body)
