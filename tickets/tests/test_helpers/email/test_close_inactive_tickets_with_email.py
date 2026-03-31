from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

from tickets.helpers.email.ticket_maintenance import close_inactive_tickets_with_email
from tickets.models import Ticket
from django.contrib.auth import get_user_model

User = get_user_model()


class TicketMaintenanceTests(TestCase):
    """Tests for ticket maintenance helper functions."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.get(username="@janedoe")

    def _make_ticket(self, **overrides):
        data = dict(
            student=self.student,
            faculty=Ticket.Faculty.choices[1][0],
            study_level=Ticket.StudyLevel.choices[1][0],
            category=Ticket.Category.choices[1][0],
            body="Test body",
        )
        data.update(overrides)
        ticket = Ticket.objects.create(**data)
        ticket.assigned_to.add(self.staff)
        return ticket

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

    def test_closes_only_inactive_awaiting_student_tickets(self):
        now = timezone.now()

        # Should close (inactive)
        t_close_1 = self._make_ticket(
            subject="Should close 1",
            status=Ticket.Status.AWAITING_STUDENT,
            awaiting_student_since=now - timedelta(days=15),
        )
        t_close_2 = self._make_ticket(
            subject="Should close 2",
            status=Ticket.Status.AWAITING_STUDENT,
            awaiting_student_since=now - timedelta(days=30),
        )

        # Should not close (too recent)
        t_recent = self._make_ticket(
            subject="Too recent",
            status=Ticket.Status.AWAITING_STUDENT,
            awaiting_student_since=now - timedelta(days=13, hours=23),
        )

        # Should not close (wrong status)
        t_wrong_status = self._make_ticket(
            subject="Wrong status",
            status=Ticket.Status.AWAITING_STAFF,
            awaiting_student_since=now - timedelta(days=20),
        )

        # Should not close (no timestamp)
        t_no_ts = self._make_ticket(
            subject="No timestamp",
            status=Ticket.Status.AWAITING_STUDENT,
            awaiting_student_since=None,
        )

        # Already closed (should remain closed, not "re-closed")
        t_already_closed = self._make_ticket(
            subject="Already closed",
            status=Ticket.Status.CLOSED,
            closed_reason=Ticket.ClosedReason.ANSWERED,
            closed_at=now - timedelta(days=1),
            awaiting_student_since=None,
        )

        updated = close_inactive_tickets_with_email(days=14)
        self.assertEqual(updated, 2)

        # Refresh and assert the two were closed correctly
        t_close_1.refresh_from_db()
        t_close_2.refresh_from_db()

        for t in (t_close_1, t_close_2):
            self.assertEqual(t.status, Ticket.Status.CLOSED)
            self.assertEqual(t.closed_reason, Ticket.ClosedReason.INACTIVITY)
            self.assertIsNotNone(t.closed_at)
            self.assertIsNone(t.awaiting_student_since)

        # Assert others unchanged
        t_recent.refresh_from_db()
        self.assertEqual(t_recent.status, Ticket.Status.AWAITING_STUDENT)
        self.assertIsNotNone(t_recent.awaiting_student_since)
        self.assertIsNone(t_recent.closed_reason)
        self.assertIsNone(t_recent.closed_at)

        t_wrong_status.refresh_from_db()
        self.assertEqual(t_wrong_status.status, Ticket.Status.AWAITING_STAFF)

        t_no_ts.refresh_from_db()
        self.assertEqual(t_no_ts.status, Ticket.Status.AWAITING_STUDENT)
        self.assertIsNone(t_no_ts.awaiting_student_since)

        t_already_closed.refresh_from_db()
        self.assertEqual(t_already_closed.status, Ticket.Status.CLOSED)
        self.assertEqual(t_already_closed.closed_reason, Ticket.ClosedReason.ANSWERED)

    def test_returns_zero_when_no_matching_tickets(self):
        updated = close_inactive_tickets_with_email(days=14)
        self.assertEqual(updated, 0)

    @override_settings(
        EMAIL_HOST_USER="c@e.com",
        EMAIL_HOST_PASSWORD="p",
        DEFAULT_FROM_EMAIL="c@e.com",
        SITE_URL="http://testserver",
    )
    def test_closes_14_day_old_ticket(self):
        ticket = self._create_awaiting_ticket(days_ago=15)
        with patch("tickets.helpers.email.email_notifications.send_mail"):
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
        with patch("tickets.helpers.email.email_notifications.send_mail") as mock_send:
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
        with patch("tickets.helpers.email.email_notifications.send_mail"):
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
            "tickets.helpers.email.email_notifications.send_mail",
            side_effect=Exception("fail"),
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
        with patch("tickets.helpers.email.email_notifications.send_mail"):
            count = close_inactive_tickets_with_email(days=14)
            self.assertEqual(count, 0)
