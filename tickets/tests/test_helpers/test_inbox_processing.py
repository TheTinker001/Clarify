"""Tests for the check_inbox management command."""

from django.test import TestCase, override_settings
from unittest.mock import patch
from email.mime.text import MIMEText
from tickets.helpers.email.inbox_processing import (
    process_email,
    decode_header_value,
    extract_body,
    extract_sender_email,
)
from tickets.tests.test_support import make_email
from tickets.models import Ticket
from django.contrib.auth import get_user_model

User = get_user_model()


class DecodeHeaderValueTest(TestCase):
    def test_plain_string(self):
        self.assertEqual(decode_header_value("Hello"), "Hello")

    def test_none_returns_empty(self):
        self.assertEqual(decode_header_value(None), "")

    def test_encoded_bytes_header(self):
        encoded = "=?utf-8?b?w5xuw69jw7Zkw6kgU8O8YmplY3Q=?="
        result = decode_header_value(encoded)
        self.assertEqual(result, "Ünïcödé Sübject")


class ExtractSenderEmailTest(TestCase):
    def test_with_angle_brackets(self):
        msg = make_email("Jane Doe <jane@test.com>", "Hi", "Body")
        self.assertEqual(extract_sender_email(msg), "jane@test.com")

    def test_plain_email(self):
        msg = make_email("jane@test.com", "Hi", "Body")
        self.assertEqual(extract_sender_email(msg), "jane@test.com")


class ExtractBodyTest(TestCase):
    def test_plain_text(self):
        msg = make_email("a@b.com", "Sub", "Hello body")
        self.assertEqual(extract_body(msg), "Hello body")

    def test_multipart(self):
        from email.mime.multipart import MIMEMultipart

        outer = MIMEMultipart()
        outer["From"] = "a@b.com"
        outer["Subject"] = "Test"
        text_part = MIMEText("Plain text body", "plain")
        html_part = MIMEText("<p>HTML body</p>", "html")
        outer.attach(text_part)
        outer.attach(html_part)
        self.assertEqual(extract_body(outer), "Plain text body")


class ExtractBodyEdgeCasesTest(TestCase):
    def test_multipart_with_no_plain_text(self):
        from email.mime.multipart import MIMEMultipart

        outer = MIMEMultipart()
        outer["From"] = "a@b.com"
        outer["Subject"] = "Test"
        html_part = MIMEText("<p>HTML only</p>", "html")
        outer.attach(html_part)
        self.assertEqual(extract_body(outer), "")

    def test_multipart_with_none_payload(self):
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase

        outer = MIMEMultipart()
        outer["From"] = "a@b.com"
        outer["Subject"] = "Test"
        attachment = MIMEBase("application", "octet-stream")
        attachment.set_payload(b"binary data")
        attachment.add_header("Content-Disposition", "attachment", filename="file.bin")
        outer.attach(attachment)
        self.assertEqual(extract_body(outer), "")


class ProcessEmailTest(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="@studenttest",
            email="student@test.com",
            password="Password123",
            first_name="Test",
            last_name="Student",
            user_type="student",
        )

    def test_creates_ticket_when_all_fields_detected(self):
        msg = make_email(
            "student@test.com",
            "Assessment deadline for undergraduate",
            "I study computer science and need an extension on my exam.",
        )
        action, detail = process_email(msg)
        self.assertEqual(action, "created")
        self.assertEqual(Ticket.objects.count(), 1)
        ticket = Ticket.objects.first()
        self.assertEqual(ticket.student, self.student)
        self.assertEqual(ticket.faculty, "nmes")
        self.assertEqual(ticket.study_level, "undergraduate")
        self.assertEqual(ticket.category, "assessment")

    def test_ignored_when_sender_not_student(self):
        msg = make_email("stranger@test.com", "Help", "I need help.")
        action, detail = process_email(msg)
        self.assertEqual(action, "ignored_not_student")
        self.assertEqual(Ticket.objects.count(), 0)

    def test_ignored_when_sender_is_staff(self):
        User.objects.create_user(
            username="@stafftest",
            email="staff@test.com",
            password="Password123",
            user_type="staff",
        )
        msg = make_email("staff@test.com", "Help", "I need help.")
        action, detail = process_email(msg)
        self.assertEqual(action, "ignored_not_student")
        self.assertEqual(Ticket.objects.count(), 0)

    def test_ignored_when_no_subject(self):
        msg = make_email("student@test.com", "", "Some body text.")
        action, detail = process_email(msg)
        self.assertEqual(action, "ignored_no_subject")
        self.assertEqual(Ticket.objects.count(), 0)

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="pass",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_missing_fields_sends_reply(self):
        msg = make_email("student@test.com", "Hello", "Just a generic question.")
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
            action, detail = process_email(msg)
            self.assertEqual(action, "missing_fields")
            self.assertEqual(Ticket.objects.count(), 0)
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            self.assertIn("student@test.com", call_kwargs["recipient_list"])
            self.assertIn("Additional Information Required", call_kwargs["subject"])

    def test_missing_fields_reply_failure_doesnt_crash(self):
        msg = make_email("student@test.com", "Hello", "Just a generic question.")
        with patch(
            "tickets.helpers.email.email_notifications.send_mail",
            side_effect=Exception("SMTP fail"),
        ):
            action, detail = process_email(msg)
            self.assertEqual(action, "missing_fields")

    def test_subject_truncated_to_78_chars(self):
        long_subject = "Assessment " + "x" * 100 + " undergraduate computer science"
        msg = make_email("student@test.com", long_subject, "Need help.")
        action, detail = process_email(msg)
        self.assertEqual(action, "created")
        ticket = Ticket.objects.first()
        self.assertEqual(len(ticket.subject), 78)

    def test_ticket_body_falls_back_to_subject_when_empty(self):
        msg = make_email(
            "student@test.com",
            "Assessment deadline undergraduate engineering",
            "",
        )
        action, detail = process_email(msg)
        self.assertEqual(action, "created")
        ticket = Ticket.objects.first()
        self.assertIn("Assessment", ticket.body)
