from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from unittest.mock import patch
from tickets.models import Ticket
from django.contrib.auth import get_user_model

User = get_user_model()


class TicketModelTestCase(TestCase):
    """Unit tests for the Ticket model."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

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
            faculty=Ticket.Faculty.NMES,
            study_level=Ticket.StudyLevel.UNDERGRADUATE,
            category=Ticket.Category.ASSESSMENT,
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

    # Tests for clean(self)
    def test_clean_accepts_student_as_student(self):
        self.ticket.student = self.student
        self._assert_ticket_is_valid()

    def test_clean_rejects_staff_as_student(self):
        self.ticket.student = self.staff
        self._assert_ticket_is_invalid()

    def test_clean_accepts_staff_as_assigned_to(self):
        self.ticket.assigned_to.add(self.staff)
        self._assert_ticket_is_valid()

    def test_clean_reject_student_as_assigned_to(self):
        self.ticket.assigned_to.add(self.student)
        self._assert_ticket_is_invalid()

    def test_clean_when_mt_five_staff_assigned(self):
        staff_users = []
        for i in range(6):
            staff = User.objects.create_user(
                username=f"@staff{i}",
                email=f"staff{i}@example.com",
                password="Password123",
                user_type=User.USER_TYPE_STAFF,
            )
            staff_users.append(staff)

        self.ticket.assigned_to.add(*staff_users)
        with self.assertRaises(ValidationError):
            self.ticket.full_clean()

    def test_clean_when_closed_requires_closed_reason(self):
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = None
        self._assert_ticket_is_invalid()

    def test_clean_closed_sets_closed_at_when_missing(self):
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.ticket.closed_at = None
        self.ticket.full_clean()

        self.assertNotEqual(self.ticket.closed_at, None)

    def test_clean_closed_does_not_override_closed_at_when_present(self):
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        current_time = timezone.now()
        self.ticket.closed_at = current_time
        self.ticket.full_clean()

        self.assertEqual(self.ticket.closed_at, current_time)

    def test_clean_when_not_closed_clears_closed_fields(self):
        self.ticket.status = Ticket.Status.AWAITING_STAFF
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.ticket.closed_at = timezone.now()
        self.ticket.full_clean()

        self.assertEqual(self.ticket.closed_reason, None)
        self.assertEqual(self.ticket.closed_at, None)

    # Tests for save(self, *args, **kwargs)
    def test_invalid_save(self):
        self.ticket.subject = "x" * 79  # Exceed the maximum allowed subject length
        with self.assertRaises(ValidationError):
            self.ticket.save()

    def test_save_closed_ticket_sets_closed_at_and_saves(self):
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.ticket.closed_at = None

        self.ticket.save()
        self.ticket.refresh_from_db()

        self.assertNotEqual(self.ticket.closed_at, None)

    # Tests for __str__(self)
    def test_str(self):
        self.assertEqual(
            str(self.ticket), f"Ticket {self.ticket.pk} | {self.ticket.subject}"
        )

    # Tests for generate_unique_url_code(self)
    def test_generate_unique_url_code_returns_non_empty_string(self):
        code = self.ticket.generate_unique_url_code()
        self.assertTrue(isinstance(code, str))
        self.assertTrue(len(code) == 10)

    def test_generate_unique_url_code_retries_on_collision(self):
        """Method must retry when token_urlsafe generates a duplicate."""
        ticket2 = Ticket.objects.create(
            student=self.student,
            faculty=Ticket.Faculty.NMES,
            study_level=Ticket.StudyLevel.UNDERGRADUATE,
            category=Ticket.Category.ASSESSMENT,
            subject="Assessment Marking Criteria",
            body="I'm unsure about the marking criteria. Can someone explain?",
            url_code="collisi",
        )

        # First call produces a collision, second call produces unique result
        with patch(
            "tickets.models.ticket.secrets.token_urlsafe",
            side_effect=["collisi", "unique4"],
        ):
            code = ticket2.generate_unique_url_code()

        self.assertEqual(code, "unique4")

    def test_ticket_priority_default_is_unassigned(self):
        ticket = Ticket.objects.create(
            student=self.student,
            faculty=Ticket.Faculty.NMES,
            study_level=Ticket.StudyLevel.UNDERGRADUATE,
            category=Ticket.Category.ASSESSMENT,
            subject="Test subject",
            body="Test body",
        )
        self.assertEqual(ticket.priority, Ticket.Priority.PENDING_PRIORITY)

    def test_invalid_ticket_priority(self):
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                student=self.student,
                faculty=Ticket.Faculty.NMES,
                study_level=Ticket.StudyLevel.UNDERGRADUATE,
                category=Ticket.Category.ASSESSMENT,
                subject="Test subject",
                body="Test body",
                priority="invalid",
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
