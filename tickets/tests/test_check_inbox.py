"""Tests for the check_inbox management command."""

from email.mime.text import MIMEText
from io import StringIO
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.core.management import call_command
from django.contrib.auth import get_user_model

from tickets.models import Ticket
from tickets.management.commands.check_inbox import (
    process_email,
    _decode_header_value,
    _extract_body,
    _extract_sender_email,
)

User = get_user_model()


def _make_email(from_addr, subject, body):
    msg = MIMEText(body)
    msg["From"] = from_addr
    msg["Subject"] = subject
    msg["To"] = "clarify@example.com"
    return msg


class DecodeHeaderValueTest(TestCase):
    def test_plain_string(self):
        self.assertEqual(_decode_header_value("Hello"), "Hello")

    def test_none_returns_empty(self):
        self.assertEqual(_decode_header_value(None), "")

    def test_encoded_bytes_header(self):
        encoded = "=?utf-8?b?w5xuw69jw7Zkw6kgU8O8YmplY3Q=?="
        result = _decode_header_value(encoded)
        self.assertEqual(result, "Ünïcödé Sübject")


class ExtractSenderEmailTest(TestCase):
    def test_with_angle_brackets(self):
        msg = _make_email("Jane Doe <jane@test.com>", "Hi", "Body")
        self.assertEqual(_extract_sender_email(msg), "jane@test.com")

    def test_plain_email(self):
        msg = _make_email("jane@test.com", "Hi", "Body")
        self.assertEqual(_extract_sender_email(msg), "jane@test.com")


class ExtractBodyTest(TestCase):
    def test_plain_text(self):
        msg = _make_email("a@b.com", "Sub", "Hello body")
        self.assertEqual(_extract_body(msg), "Hello body")

    def test_multipart(self):
        from email.mime.multipart import MIMEMultipart

        outer = MIMEMultipart()
        outer["From"] = "a@b.com"
        outer["Subject"] = "Test"
        text_part = MIMEText("Plain text body", "plain")
        html_part = MIMEText("<p>HTML body</p>", "html")
        outer.attach(text_part)
        outer.attach(html_part)
        self.assertEqual(_extract_body(outer), "Plain text body")


class ExtractBodyEdgeCasesTest(TestCase):
    def test_multipart_with_no_plain_text(self):
        from email.mime.multipart import MIMEMultipart

        outer = MIMEMultipart()
        outer["From"] = "a@b.com"
        outer["Subject"] = "Test"
        html_part = MIMEText("<p>HTML only</p>", "html")
        outer.attach(html_part)
        self.assertEqual(_extract_body(outer), "")

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
        self.assertEqual(_extract_body(outer), "")


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
        msg = _make_email(
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
        msg = _make_email("stranger@test.com", "Help", "I need help.")
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
        msg = _make_email("staff@test.com", "Help", "I need help.")
        action, detail = process_email(msg)
        self.assertEqual(action, "ignored_not_student")
        self.assertEqual(Ticket.objects.count(), 0)

    def test_ignored_when_no_subject(self):
        msg = _make_email("student@test.com", "", "Some body text.")
        action, detail = process_email(msg)
        self.assertEqual(action, "ignored_no_subject")
        self.assertEqual(Ticket.objects.count(), 0)

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="pass",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_missing_fields_sends_reply(self):
        msg = _make_email("student@test.com", "Hello", "Just a generic question.")
        with patch("tickets.management.commands.check_inbox.send_mail") as mock_send:
            action, detail = process_email(msg)
            self.assertEqual(action, "missing_fields")
            self.assertEqual(Ticket.objects.count(), 0)
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            self.assertIn("student@test.com", call_kwargs["recipient_list"])
            self.assertIn("Additional Information Required", call_kwargs["subject"])

    def test_missing_fields_reply_failure_doesnt_crash(self):
        msg = _make_email("student@test.com", "Hello", "Just a generic question.")
        with patch(
            "tickets.management.commands.check_inbox.send_mail",
            side_effect=Exception("SMTP fail"),
        ):
            action, detail = process_email(msg)
            self.assertEqual(action, "missing_fields")

    def test_subject_truncated_to_78_chars(self):
        long_subject = "Assessment " + "x" * 100 + " undergraduate computer science"
        msg = _make_email("student@test.com", long_subject, "Need help.")
        action, detail = process_email(msg)
        self.assertEqual(action, "created")
        ticket = Ticket.objects.first()
        self.assertEqual(len(ticket.subject), 78)

    def test_ticket_body_falls_back_to_subject_when_empty(self):
        msg = _make_email(
            "student@test.com",
            "Assessment deadline undergraduate engineering",
            "",
        )
        action, detail = process_email(msg)
        self.assertEqual(action, "created")
        ticket = Ticket.objects.first()
        self.assertIn("Assessment", ticket.body)


@override_settings(
    IMAP_HOST="imap.test.com",
    IMAP_PORT=993,
    IMAP_USER="test@test.com",
    IMAP_PASSWORD="password",
)
class CheckInboxCommandTest(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="@cmdstudent",
            email="cmdstudent@test.com",
            password="Password123",
            first_name="Cmd",
            last_name="Student",
            user_type="student",
        )

    @patch("tickets.management.commands.check_inbox.imaplib.IMAP4_SSL")
    def test_no_unread_emails(self, mock_imap_class):
        mock_mail = MagicMock()
        mock_imap_class.return_value = mock_mail
        mock_mail.search.return_value = ("OK", [b""])
        mock_mail.select.return_value = ("OK", [b"1"])

        out = StringIO()
        call_command("check_inbox", stdout=out)
        self.assertIn("No new emails", out.getvalue())
        mock_mail.logout.assert_called_once()

    @patch("tickets.management.commands.check_inbox.imaplib.IMAP4_SSL")
    def test_processes_unread_email_and_creates_ticket(self, mock_imap_class):
        msg = _make_email(
            "cmdstudent@test.com",
            "Assessment question undergraduate engineering",
            "I need help with my computer science exam.",
        )
        raw = msg.as_bytes()

        mock_mail = MagicMock()
        mock_imap_class.return_value = mock_mail
        mock_mail.select.return_value = ("OK", [b"1"])
        mock_mail.search.return_value = ("OK", [b"1"])
        mock_mail.fetch.return_value = ("OK", [(b"1", raw)])

        out = StringIO()
        call_command("check_inbox", stdout=out)
        self.assertIn("Ticket created", out.getvalue())
        self.assertEqual(Ticket.objects.count(), 1)
        mock_mail.logout.assert_called_once()

    @patch("tickets.management.commands.check_inbox.imaplib.IMAP4_SSL")
    def test_imap_connection_failure(self, mock_imap_class):
        mock_imap_class.side_effect = Exception("Connection refused")

        err = StringIO()
        call_command("check_inbox", stderr=err)
        self.assertIn("Failed to connect", err.getvalue())

    @override_settings(IMAP_USER="", IMAP_PASSWORD="")
    def test_skips_when_no_credentials(self):
        err = StringIO()
        call_command("check_inbox", stderr=err)
        self.assertIn("not configured", err.getvalue())

    @patch("tickets.management.commands.check_inbox.imaplib.IMAP4_SSL")
    def test_fetch_failure_skips_email(self, mock_imap_class):
        mock_mail = MagicMock()
        mock_imap_class.return_value = mock_mail
        mock_mail.select.return_value = ("OK", [b"1"])
        mock_mail.search.return_value = ("OK", [b"1"])
        mock_mail.fetch.return_value = ("FAIL", [])

        out = StringIO()
        call_command("check_inbox", stdout=out)
        self.assertEqual(Ticket.objects.count(), 0)
        mock_mail.logout.assert_called_once()

    @patch("tickets.management.commands.check_inbox.imaplib.IMAP4_SSL")
    def test_missing_fields_output(self, mock_imap_class):
        msg = _make_email("cmdstudent@test.com", "Hello", "Just a generic question.")
        raw = msg.as_bytes()

        mock_mail = MagicMock()
        mock_imap_class.return_value = mock_mail
        mock_mail.select.return_value = ("OK", [b"1"])
        mock_mail.search.return_value = ("OK", [b"1"])
        mock_mail.fetch.return_value = ("OK", [(b"1", raw)])

        out = StringIO()
        call_command("check_inbox", stdout=out)
        self.assertIn("Missing fields", out.getvalue())
        self.assertEqual(Ticket.objects.count(), 0)

    @patch("tickets.management.commands.check_inbox.imaplib.IMAP4_SSL")
    def test_ignored_no_subject_output(self, mock_imap_class):
        msg = _make_email("cmdstudent@test.com", "", "Some body.")
        raw = msg.as_bytes()

        mock_mail = MagicMock()
        mock_imap_class.return_value = mock_mail
        mock_mail.select.return_value = ("OK", [b"1"])
        mock_mail.search.return_value = ("OK", [b"1"])
        mock_mail.fetch.return_value = ("OK", [(b"1", raw)])

        out = StringIO()
        call_command("check_inbox", stdout=out)
        self.assertIn("no subject", out.getvalue())
        self.assertEqual(Ticket.objects.count(), 0)

    @patch("tickets.management.commands.check_inbox.imaplib.IMAP4_SSL")
    def test_processes_multiple_emails(self, mock_imap_class):
        msg1 = _make_email(
            "cmdstudent@test.com",
            "Assessment question undergraduate engineering",
            "Computer science exam help.",
        )
        msg2 = _make_email(
            "stranger@test.com",
            "Help",
            "Need help.",
        )
        mock_mail = MagicMock()
        mock_imap_class.return_value = mock_mail
        mock_mail.select.return_value = ("OK", [b"1"])
        mock_mail.search.return_value = ("OK", [b"1 2"])
        mock_mail.fetch.side_effect = [
            ("OK", [(b"1", msg1.as_bytes())]),
            ("OK", [(b"2", msg2.as_bytes())]),
        ]

        out = StringIO()
        call_command("check_inbox", stdout=out)
        output = out.getvalue()
        self.assertIn("Ticket created", output)
        self.assertIn("not a student", output)
        self.assertIn("Done", output)
        self.assertEqual(Ticket.objects.count(), 1)

    @patch("tickets.management.commands.check_inbox.imaplib.IMAP4_SSL")
    def test_ignores_non_student_email(self, mock_imap_class):
        msg = _make_email("stranger@test.com", "Help", "Need help.")
        raw = msg.as_bytes()

        mock_mail = MagicMock()
        mock_imap_class.return_value = mock_mail
        mock_mail.select.return_value = ("OK", [b"1"])
        mock_mail.search.return_value = ("OK", [b"1"])
        mock_mail.fetch.return_value = ("OK", [(b"1", raw)])

        out = StringIO()
        call_command("check_inbox", stdout=out)
        self.assertIn("not a student", out.getvalue())
        self.assertEqual(Ticket.objects.count(), 0)
