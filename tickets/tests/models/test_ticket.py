from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from tickets.models import Ticket

User = get_user_model()


class TicketModelTestCase(TestCase):
    """Unit tests for the Ticket model."""

    def setUp(self):
        self.student = User.objects.create_user(
            username="student007",
            email="student007@example.com",
            password="Password123",
            user_type=User.USER_TYPE_STUDENT,
        )
        self.staff = User.objects.create_user(
            username="staff007",
            email="staff007@example.com",
            password="Password123",
            user_type=User.USER_TYPE_STAFF,
        )
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="assessment",
            subject="Assessment Marking Criteria",
            body="I'm unsure about the marking criteria. Can someone explain?",
        )

    def _assert_ticket_is_valid(self):
        self.ticket.full_clean()

    def _assert_ticket_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.ticket.full_clean()

    def test_subject_can_be_78_characters_long(self):
        self.ticket.subject = "x" * 78
        self._assert_ticket_is_valid()

    def test_subject_cannot_be_over_78_characters_long(self):
        self.ticket.subject = "x" * 79
        self._assert_ticket_is_invalid()

    def test_body_can_be_50000_characters_long(self):
        self.ticket.body = "x" * 50000
        self._assert_ticket_is_valid()

    def test_body_cannot_be_over_50000_characters_long(self):
        self.ticket.body = "x" * 50001
        self._assert_ticket_is_invalid()

    # Tests for clean(self)
    def test_clean_accepts_student_as_student(self):
        self.ticket.student = self.student
        self._assert_ticket_is_valid()

    def test_clean_rejects_staff_as_student(self):
        self.ticket.student = self.staff
        self._assert_ticket_is_invalid()

    def test_clean_accepts_staff_as_assigned_to(self):
        self.ticket.assigned_to = self.staff
        self._assert_ticket_is_valid()

    def test_clean_reject_student_as_assigned_to(self):
        self.ticket.assigned_to = self.student
        self._assert_ticket_is_invalid()

    def test_clean_when_closed_requires_closed_reason(self):
        self.ticket.status = "closed"
        self.ticket.closed_reason = None
        self._assert_ticket_is_invalid()

    def test_clean_closed_sets_closed_at_when_missing(self):
        self.ticket.status = "closed"
        self.ticket.closed_reason = "answered"
        self.ticket.closed_at = None
        self.ticket.full_clean()

        self.assertNotEqual(self.ticket.closed_at, None)

    def test_clean_closed_does_not_override_closed_at_when_present(self):
        self.ticket.status = "closed"
        self.ticket.closed_reason = "answered"
        current_time = timezone.now()
        self.ticket.closed_at = current_time
        self.ticket.full_clean()

        self.assertEqual(self.ticket.closed_at, current_time)

    def test_clean_when_not_closed_clears_closed_fields(self):
        self.ticket.status = "awaiting_staff"
        self.ticket.closed_reason = "answered"
        self.ticket.closed_at = timezone.now()
        self.ticket.full_clean()

        self.assertEqual(self.ticket.closed_reason, None)
        self.assertEqual(self.ticket.closed_at, None)

    # Tests for save(self, *args, **kwargs)
    def test_invalid_save(self):
        self.ticket.subject = "x" * 79  # invalid subject length
        with self.assertRaises(ValidationError):
            self.ticket.save()

    def test_save_closed_ticket_sets_closed_at_and_saves(self):
        self.ticket.status = "closed"
        self.ticket.closed_reason = "answered"
        self.ticket.closed_at = None

        self.ticket.save()
        self.ticket.refresh_from_db()

        self.assertNotEqual(self.ticket.closed_at, None)

    # Tests for __str__(self)
    def test_str(self):
        self.assertEqual(
            str(self.ticket), f"Ticket {self.ticket.pk} | {self.ticket.subject}"
        )
