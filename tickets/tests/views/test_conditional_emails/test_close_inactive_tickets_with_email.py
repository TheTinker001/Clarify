"""Tests for conditional email helper: close_inactive_tickets_with_email"""

from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from tickets.conditional_emails import close_inactive_tickets_with_email
from tickets.models import Ticket
from django.contrib.auth import get_user_model

User = get_user_model()


class CloseInactiveTicketsWithEmailTest(TestCase):
    """Tests for conditional email helper: close_inactive_tickets_with_email"""

    def setUp(self):
        self.student = User.objects.create_user(
            username="@inactivestudent",
            email="inactive@test.com",
            password="Password123",
            first_name="Inactive",
            last_name="Student",
            user_type="student",
        )

    def _create_awaiting_ticket(self, days_ago):
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Inactive ticket",
            body="Body.",
            status=Ticket.Status.AWAITING_STUDENT,
        )
        Ticket.objects.filter(pk=ticket.pk).update(
            awaiting_student_since=timezone.now() - timedelta(days=days_ago),
        )
        return ticket

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
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

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
    def test_sends_inactivity_email_on_close(self):
        self._create_awaiting_ticket(days_ago=15)
        with patch("tickets.conditional_emails.send_mail") as mock_send:
            close_inactive_tickets_with_email(days=14)
            mock_send.assert_called_once()
            self.assertIn("inactivity", mock_send.call_args.kwargs["message"].lower())

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
    def test_skips_ticket_less_than_14_days(self):
        self._create_awaiting_ticket(days_ago=10)
        with patch("tickets.conditional_emails.send_mail"):
            count = close_inactive_tickets_with_email(days=14)
            self.assertEqual(count, 0)

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
    def test_email_failure_doesnt_prevent_close(self):
        ticket = self._create_awaiting_ticket(days_ago=15)
        with patch(
            "tickets.conditional_emails.send_mail", side_effect=Exception("fail")
        ):
            count = close_inactive_tickets_with_email(days=14)
            self.assertEqual(count, 1)
            ticket.refresh_from_db()
            self.assertEqual(ticket.status, Ticket.Status.CLOSED)

    def test_skips_already_closed_tickets(self):
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Already closed",
            body="Body.",
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
