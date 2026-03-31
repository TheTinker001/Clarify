"""Tests for the check_inbox management command."""

from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from io import StringIO
from django.core.management import call_command
from tickets.tests.support import make_email
from tickets.models import Ticket
from django.contrib.auth import get_user_model

User = get_user_model()


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
        msg = make_email(
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
        msg = make_email("cmdstudent@test.com", "Hello", "Just a generic question.")
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
        msg = make_email("cmdstudent@test.com", "", "Some body.")
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
        msg1 = make_email(
            "cmdstudent@test.com",
            "Assessment question undergraduate engineering",
            "Computer science exam help.",
        )
        msg2 = make_email(
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
        msg = make_email("stranger@test.com", "Help", "Need help.")
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
