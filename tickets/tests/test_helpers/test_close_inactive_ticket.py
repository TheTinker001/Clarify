from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from tickets.conditional_emails import close_inactive_tickets_with_email
from tickets.models import Ticket, User


class CloseInactiveTicketsTests(TestCase):
    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.get(username="@janedoe")

    def test_closes_only_inactive_awaiting_student_tickets(self):
        now = timezone.now()

        # Should close (inactive)
        t_close_1 = self.make_ticket(
            subject="Should close 1",
            status=Ticket.Status.AWAITING_STUDENT,
            awaiting_student_since=now - timedelta(days=15),
        )
        t_close_2 = self.make_ticket(
            subject="Should close 2",
            status=Ticket.Status.AWAITING_STUDENT,
            awaiting_student_since=now - timedelta(days=30),
        )

        # Should not close (too recent)
        t_recent = self.make_ticket(
            subject="Too recent",
            status=Ticket.Status.AWAITING_STUDENT,
            awaiting_student_since=now - timedelta(days=13, hours=23),
        )

        # Should not close (wrong status)
        t_wrong_status = self.make_ticket(
            subject="Wrong status",
            status=Ticket.Status.AWAITING_STAFF,
            awaiting_student_since=now - timedelta(days=20),
        )

        # Should not close (no timestamp)
        t_no_ts = self.make_ticket(
            subject="No timestamp",
            status=Ticket.Status.AWAITING_STUDENT,
            awaiting_student_since=None,
        )

        # Already closed (should remain closed, not "re-closed")
        t_already_closed = self.make_ticket(
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

    def make_ticket(self, **overrides):
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
