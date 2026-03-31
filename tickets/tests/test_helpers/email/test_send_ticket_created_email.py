from django.test import TestCase, override_settings
from unittest.mock import patch
from tickets.models import Ticket, Comment
from tickets.helpers.email.email_notifications import (
    send_ticket_created_email,
    send_staff_comment_email,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class SendTicketCreatedEmailTest(TestCase):
    """Tests for the send_ticket_created_email and send_staff_comment_email helper function."""

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
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_ticket_created_email(self.ticket)
            mock_send.assert_not_called()

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="",
    )
    def test_no_email_sent_when_email_host_password_is_empty(self):
        """Email is not sent when EMAIL_HOST_PASSWORD is empty."""
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_ticket_created_email(self.ticket)
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
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_ticket_created_email(self.ticket)
            mock_send.assert_not_called()

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_email_sent_with_correct_subject(self):
        """Email is sent with the correct subject line."""
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_ticket_created_email(self.ticket)
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
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_ticket_created_email(self.ticket)
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
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_ticket_created_email(self.ticket)
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
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_ticket_created_email(self.ticket)
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
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_ticket_created_email(self.ticket)
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            self.assertEqual(call_kwargs["from_email"], "clarify@example.com")

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_email_body_uses_student_when_no_first_name(self):
        """Email body uses 'stiudent' when student has no first name."""
        self.student.first_name = ""
        self.student.save()
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_ticket_created_email(self.ticket)
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            body = call_kwargs["message"]
            self.assertIn("Dear student", body)


class SendStaffResponseEmailTest(TestCase):
    """Tests for the send_staff_comment_email helper function."""

    def setUp(self):
        self.student = User.objects.create_user(
            username="@teststudent2",
            email="student2@test.com",
            password="Password123",
            first_name="Jane",
            last_name="Student",
            user_type="student",
        )
        self.staff = User.objects.create_user(
            username="@teststaff",
            email="staff@test.com",
            password="Password123",
            first_name="Staff",
            last_name="Member",
            user_type="staff",
        )
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="My query",
            body="Need help.",
        )
        self.response_obj = Comment.objects.create(
            ticket=self.ticket,
            author=self.staff,
            body="Here is your answer.",
        )

    @override_settings(EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD="")
    def test_no_email_when_host_user_empty(self):
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_staff_comment_email(self.ticket, self.response_obj)
            mock_send.assert_not_called()

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
        SITE_URL="http://testserver",
    )
    def test_no_email_when_student_has_no_email(self):
        self.student.email = ""
        self.student.save()
        self.ticket.refresh_from_db()
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_staff_comment_email(self.ticket, self.response_obj)
            mock_send.assert_not_called()

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
        SITE_URL="http://testserver",
    )
    def test_email_sent_to_student(self):
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_staff_comment_email(self.ticket, self.response_obj)
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            self.assertEqual(call_kwargs["recipient_list"], ["student2@test.com"])

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
        SITE_URL="http://testserver",
    )
    def test_email_subject_contains_ticket_subject(self):
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_staff_comment_email(self.ticket, self.response_obj)
            call_kwargs = mock_send.call_args.kwargs
            self.assertIn("My query", call_kwargs["subject"])

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
        SITE_URL="http://testserver",
    )
    def test_email_body_contains_response_text(self):
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_staff_comment_email(self.ticket, self.response_obj)
            call_kwargs = mock_send.call_args.kwargs
            self.assertIn("Here is your answer.", call_kwargs["message"])

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
        SITE_URL="http://testserver",
    )
    def test_email_body_contains_ticket_link(self):
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_staff_comment_email(self.ticket, self.response_obj)
            call_kwargs = mock_send.call_args.kwargs
            expected_url = f"http://testserver/ticket/{self.ticket.url_code}/"
            self.assertIn(expected_url, call_kwargs["message"])

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
        SITE_URL="http://testserver",
    )
    def test_email_body_uses_student_when_no_first_name(self):
        self.student.first_name = ""
        self.student.save()
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_staff_comment_email(self.ticket, self.response_obj)
            call_kwargs = mock_send.call_args.kwargs
            self.assertIn("Dear student", call_kwargs["message"])

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="",
        SITE_URL="http://testserver",
    )
    def test_email_falls_back_to_host_user_when_no_default_from(self):
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            send_staff_comment_email(self.ticket, self.response_obj)
            call_kwargs = mock_send.call_args.kwargs
            self.assertEqual(call_kwargs["from_email"], "clarify@example.com")
