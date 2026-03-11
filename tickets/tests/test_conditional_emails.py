"""Tests for conditional email helpers: reminders and closure notifications."""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from tickets.conditional_emails import (
    _send_reminder_email,
    _send_ticket_closed_email,
    send_reminder_emails,
    close_inactive_tickets_with_email,
)
from tickets.models import Ticket

User = get_user_model()


class SendReminderEmailTest(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username="@remindstudent", email="remind@test.com",
            password="Password123", first_name="Remind", last_name="Me",
            user_type="student",
        )
        self.ticket = Ticket.objects.create(
            student=self.student, faculty="kbs", study_level="undergraduate",
            category="other", subject="Need help", body="Body.",
        )

    @override_settings(EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD="")
    def test_no_email_when_no_credentials(self):
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            _send_reminder_email(self.ticket)
            mock_send.assert_not_called()

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_no_email_when_student_has_no_email(self):
        self.student.email = ""
        self.student.save()
        self.ticket.refresh_from_db()
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            _send_reminder_email(self.ticket)
            mock_send.assert_not_called()

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_reminder_email_sent(self):
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            _send_reminder_email(self.ticket)
            mock_send.assert_called_once()
            kw = mock_send.call_args.kwargs
            self.assertIn("remind@test.com", kw["recipient_list"])
            self.assertIn("Reminder", kw["subject"])
            self.assertIn(self.ticket.url_code, kw["message"])
            self.assertIn("Need help", kw["subject"])


class SendTicketClosedEmailTest(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username="@closestudent", email="close@test.com",
            password="Password123", first_name="Close", last_name="Me",
            user_type="student",
        )
        self.ticket = Ticket.objects.create(
            student=self.student, faculty="kbs", study_level="undergraduate",
            category="other", subject="My query", body="Body.",
        )

    @override_settings(EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD="")
    def test_no_email_when_no_credentials(self):
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            _send_ticket_closed_email(self.ticket, "answered")
            mock_send.assert_not_called()

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_no_email_when_student_has_no_email(self):
        self.student.email = ""
        self.student.save()
        self.ticket.refresh_from_db()
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            _send_ticket_closed_email(self.ticket, "answered")
            mock_send.assert_not_called()

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_closed_answered_email(self):
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            _send_ticket_closed_email(self.ticket, "answered")
            mock_send.assert_called_once()
            kw = mock_send.call_args.kwargs
            self.assertIn("close@test.com", kw["recipient_list"])
            self.assertIn("closed", kw["subject"].lower())
            self.assertIn("answered", kw["message"].lower())

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_closed_inactivity_email(self):
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            _send_ticket_closed_email(self.ticket, "inactivity")
            mock_send.assert_called_once()
            kw = mock_send.call_args.kwargs
            self.assertIn("inactivity", kw["message"].lower())

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="", SITE_URL="http://testserver")
    def test_falls_back_to_host_user_when_no_default_from(self):
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            _send_ticket_closed_email(self.ticket, "answered")
            self.assertEqual(mock_send.call_args.kwargs["from_email"], "c@e.com")


class SendReminderEmailsTest(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username="@bulkstudent", email="bulk@test.com",
            password="Password123", first_name="Bulk", last_name="Student",
            user_type="student",
        )

    def _create_awaiting_ticket(self, days_ago, reminder_sent=False):
        ticket = Ticket.objects.create(
            student=self.student, faculty="kbs", study_level="undergraduate",
            category="other", subject="Old ticket", body="Body.",
            status=Ticket.Status.AWAITING_STUDENT,
        )
        Ticket.objects.filter(pk=ticket.pk).update(
            awaiting_student_since=timezone.now() - timedelta(days=days_ago),
            reminder_sent_at=timezone.now() if reminder_sent else None,
        )
        return ticket

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_sends_reminder_for_7_day_old_ticket(self):
        self._create_awaiting_ticket(days_ago=8)
        with patch("tickets.conditional_emails.send_mail"):
            count = send_reminder_emails(days=7)
            self.assertEqual(count, 1)

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_skips_ticket_with_reminder_already_sent(self):
        self._create_awaiting_ticket(days_ago=8, reminder_sent=True)
        with patch("tickets.conditional_emails.send_mail"):
            count = send_reminder_emails(days=7)
            self.assertEqual(count, 0)

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_skips_ticket_less_than_7_days(self):
        self._create_awaiting_ticket(days_ago=5)
        with patch("tickets.conditional_emails.send_mail"):
            count = send_reminder_emails(days=7)
            self.assertEqual(count, 0)

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_sets_reminder_sent_at_after_sending(self):
        ticket = self._create_awaiting_ticket(days_ago=8)
        with patch("tickets.conditional_emails.send_mail"):
            send_reminder_emails(days=7)
            ticket.refresh_from_db()
            self.assertIsNotNone(ticket.reminder_sent_at)

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_email_failure_doesnt_crash(self):
        self._create_awaiting_ticket(days_ago=8)
        with patch("tickets.conditional_emails.send_mail", side_effect=Exception("fail")):
            count = send_reminder_emails(days=7)
            self.assertEqual(count, 0)

    def test_skips_closed_tickets(self):
        ticket = Ticket.objects.create(
            student=self.student, faculty="kbs", study_level="undergraduate",
            category="other", subject="Closed", body="Body.",
            status=Ticket.Status.CLOSED,
            closed_reason=Ticket.ClosedReason.ANSWERED,
            closed_at=timezone.now(),
        )
        Ticket.objects.filter(pk=ticket.pk).update(
            awaiting_student_since=timezone.now() - timedelta(days=10),
        )
        with patch("tickets.conditional_emails.send_mail"):
            count = send_reminder_emails(days=7)
            self.assertEqual(count, 0)


class CloseInactiveTicketsWithEmailTest(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username="@inactivestudent", email="inactive@test.com",
            password="Password123", first_name="Inactive", last_name="Student",
            user_type="student",
        )

    def _create_awaiting_ticket(self, days_ago):
        ticket = Ticket.objects.create(
            student=self.student, faculty="kbs", study_level="undergraduate",
            category="other", subject="Inactive ticket", body="Body.",
            status=Ticket.Status.AWAITING_STUDENT,
        )
        Ticket.objects.filter(pk=ticket.pk).update(
            awaiting_student_since=timezone.now() - timedelta(days=days_ago),
        )
        return ticket

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_closes_14_day_old_ticket(self):
        ticket = self._create_awaiting_ticket(days_ago=15)
        with patch("tickets.conditional_emails.send_mail"):
            count = close_inactive_tickets_with_email(days=14)
            self.assertEqual(count, 1)
            ticket.refresh_from_db()
            self.assertEqual(ticket.status, Ticket.Status.CLOSED)
            self.assertEqual(ticket.closed_reason, Ticket.ClosedReason.INACTIVITY)
            self.assertIsNotNone(ticket.closed_at)
            self.assertIsNone(ticket.awaiting_student_since)
            self.assertIsNone(ticket.reminder_sent_at)

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_sends_inactivity_email_on_close(self):
        self._create_awaiting_ticket(days_ago=15)
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            close_inactive_tickets_with_email(days=14)
            mock_send.assert_called_once()
            self.assertIn("inactivity", mock_send.call_args.kwargs["message"].lower())

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_skips_ticket_less_than_14_days(self):
        self._create_awaiting_ticket(days_ago=10)
        with patch("tickets.conditional_emails.send_mail"):
            count = close_inactive_tickets_with_email(days=14)
            self.assertEqual(count, 0)

    @override_settings(EMAIL_HOST_USER="c@e.com", EMAIL_HOST_PASSWORD="p", DEFAULT_FROM_EMAIL="c@e.com", SITE_URL="http://testserver")
    def test_email_failure_doesnt_prevent_close(self):
        ticket = self._create_awaiting_ticket(days_ago=15)
        with patch("tickets.conditional_emails.send_mail", side_effect=Exception("fail")):
            count = close_inactive_tickets_with_email(days=14)
            self.assertEqual(count, 1)
            ticket.refresh_from_db()
            self.assertEqual(ticket.status, Ticket.Status.CLOSED)

    def test_skips_already_closed_tickets(self):
        ticket = Ticket.objects.create(
            student=self.student, faculty="kbs", study_level="undergraduate",
            category="other", subject="Already closed", body="Body.",
            status=Ticket.Status.CLOSED,
            closed_reason=Ticket.ClosedReason.ANSWERED,
            closed_at=timezone.now(),
        )
        Ticket.objects.filter(pk=ticket.pk).update(
            awaiting_student_since=timezone.now() - timedelta(days=20),
        )
        with patch("tickets.conditional_emails.send_mail"):
            count = close_inactive_tickets_with_email(days=14)
            self.assertEqual(count, 0)
