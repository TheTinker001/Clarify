"""Tests for conditional email helper: send_reminder_emails"""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from tickets.conditional_emails import send_reminder_emails
from tickets.models import Ticket

User = get_user_model()


class SendReminderEmailsTest(TestCase):
    """Tests for conditional email helper: send_reminder_emails"""

    def setUp(self):
        self.student = User.objects.create_user(
            username="@bulkstudent",
            email="bulk@test.com",
            password="Password123",
            first_name="Bulk",
            last_name="Student",
            user_type="student",
        )

    def _create_awaiting_ticket(self, days_ago, reminder_sent=False):
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Old ticket",
            body="Body.",
            status=Ticket.Status.AWAITING_STUDENT,
        )
        Ticket.objects.filter(pk=ticket.pk).update(
            awaiting_student_since=timezone.now() - timedelta(days=days_ago),
            reminder_sent_at=timezone.now() if reminder_sent else None,
        )
        return ticket

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
    def test_sends_reminder_for_7_day_old_ticket(self):
        self._create_awaiting_ticket(days_ago=8)
        with patch("tickets.conditional_emails.send_mail"):
            count = send_reminder_emails(days=7)
            self.assertEqual(count, 1)

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
    def test_skips_ticket_with_reminder_already_sent(self):
        self._create_awaiting_ticket(days_ago=8, reminder_sent=True)
        with patch("tickets.conditional_emails.send_mail"):
            count = send_reminder_emails(days=7)
            self.assertEqual(count, 0)

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
    def test_skips_ticket_less_than_7_days(self):
        self._create_awaiting_ticket(days_ago=5)
        with patch("tickets.conditional_emails.send_mail"):
            count = send_reminder_emails(days=7)
            self.assertEqual(count, 0)

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
    def test_sets_reminder_sent_at_after_sending(self):
        ticket = self._create_awaiting_ticket(days_ago=8)
        with patch("tickets.conditional_emails.send_mail"):
            send_reminder_emails(days=7)
            ticket.refresh_from_db()
            self.assertIsNotNone(ticket.reminder_sent_at)

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
    def test_email_failure_doesnt_crash(self):
        self._create_awaiting_ticket(days_ago=8)
        with patch(
            "tickets.conditional_emails.send_mail", side_effect=Exception("fail")
        ):
            count = send_reminder_emails(days=7)
            self.assertEqual(count, 0)

    def test_skips_closed_tickets(self):
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Closed",
            body="Body.",
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
