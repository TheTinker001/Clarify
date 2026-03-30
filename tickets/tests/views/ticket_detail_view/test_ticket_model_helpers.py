"""Tests ticket model helper functions."""

from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from tickets.models import Ticket
from django.contrib.auth import get_user_model

User = get_user_model()


class TicketModelHelpersTest(TestCase):
    """Tests ticket model helper functions."""

    def setUp(self):
        self.student = User.objects.create_user(
            username="@modelstudent",
            email="model@test.com",
            password="Password123",
            user_type="student",
        )

    @override_settings(TICKET_EDIT_WINDOW_MINUTES=10)
    def test_is_editable_by_student_within_window(self):
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Test",
            body="Body.",
        )
        self.assertTrue(ticket.is_editable_by_student())

    @override_settings(TICKET_EDIT_WINDOW_MINUTES=10)
    def test_is_not_editable_after_window(self):
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Test",
            body="Body.",
        )
        Ticket.objects.filter(pk=ticket.pk).update(
            created_at=timezone.now() - timedelta(minutes=11)
        )
        ticket.refresh_from_db()
        self.assertFalse(ticket.is_editable_by_student())

    @override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=15)
    def test_is_visible_to_staff_after_delay(self):
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Test",
            body="Body.",
        )
        Ticket.objects.filter(pk=ticket.pk).update(
            created_at=timezone.now() - timedelta(minutes=16)
        )
        ticket.refresh_from_db()
        self.assertTrue(ticket.is_visible_to_staff())

    @override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=15)
    def test_is_not_visible_to_staff_before_delay(self):
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Test",
            body="Body.",
        )
        self.assertFalse(ticket.is_visible_to_staff())
