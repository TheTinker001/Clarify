"""Tests for the ticket detail view."""

from django.test import TestCase
from tickets.forms import TicketPriorityForm, TicketFieldsForm
from tickets.models import Ticket, User
from tickets.tests.helpers import (
    MenuTesterMixin,
    _reverse_with_next,
    _valid_comment_post_data,
)

from datetime import timedelta
from django.utils import timezone


class TicketDetailViewTestCase(TestCase, MenuTesterMixin):
    """Test suite for the ticket detail view."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.student2 = User.objects.get(username="@petrapickles")
        self.staff = User.objects.get(username="@janedoe")
        self.ticket = Ticket.objects.create(
            student=self.student,
            assigned_to=self.staff,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Update card access",
            body="Card access not working for lab.",
        )
        self.url = self.ticket.get_absolute_url()

    def test_ticket_detail_url(self):
        self.assertEqual(self.url, f"/ticket/{self.ticket.url_code}/")

    def test_get_ticket_detail_redirects_when_not_logged_in(self):
        redirect_url = _reverse_with_next("log_in", self.url)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )

    def test_get_ticket_detail(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ticket_detail.html")
        self.assertEqual(response.context["ticket"], self.ticket)
        self.assertContains(response, self.ticket.subject)
        self.assertContains(response, self.ticket.body)
        self.assert_menu(response)

    def test_ticket_detail_returns_404_for_missing_ticket(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get("/ticket/jujutsu/")
        self.assertEqual(response.status_code, 404)

    def test_user_is_not_owner_nor_staff(self):
        self.client.login(username=self.student2.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_post_set_priority_as_non_staff(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(
            self.url,
            data={"action": "set_priority", "priority": Ticket.Priority.HIGH},
        )
        self.assertEqual(response.status_code, 404)

    def test_priority_form_in_context_for_staff(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertIn("ticket_priority_form", response.context)
        self.assertIsInstance(
            response.context["ticket_priority_form"], TicketPriorityForm
        )

    def test_priority_form_not_in_context_for_non_staff(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertIsNone(response.context.get("ticket_priority_form"))

    def test_post_set_priority_on_closed_ticket(self):
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.ticket.closed_at = timezone.now()
        self.ticket.save()
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(
            self.url,
            data={"action": "set_priority", "priority": Ticket.Priority.HIGH},
        )
        self.assertEqual(response.status_code, 404)

    def test_post_invalid_priority(self):
        self.client.login(username=self.staff.username, password="Password123")
        initial_priority = self.ticket.priority
        response = self.client.post(
            self.url, data={"action": "set_priority", "priority": "invalid_priority"}
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.priority, initial_priority)
        self.assertEqual(response.status_code, 302)

    def test_ticket_tags_displayed_in_ticket_detail(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, self.ticket.get_faculty_display(), html=True)
        self.assertContains(response, self.ticket.get_study_level_display(), html=True)
        self.assertContains(response, self.ticket.get_category_display(), html=True)

    def test_post_different_valid_priorities(self):
        self.client.login(username=self.staff.username, password="Password123")
        for priority in [
            Ticket.Priority.LOW,
            Ticket.Priority.MEDIUM,
            Ticket.Priority.HIGH,
            Ticket.Priority.PENDING_PRIORITY,
        ]:
            response = self.client.post(
                self.url, data={"action": "set_priority", "priority": priority}
            )
            self.assertRedirects(response, self.ticket.get_absolute_url())
            self.ticket.refresh_from_db()
            self.assertEqual(self.ticket.priority, priority)

    def test_post_close_ticket_as_staff_closes_ticket_as_answered(self):
        self.client.login(username=self.staff.username, password="Password123")

        self.ticket.status = Ticket.Status.AWAITING_STUDENT
        self.ticket.awaiting_student_since = timezone.now() - timedelta(days=1)
        self.ticket.closed_reason = None
        self.ticket.closed_at = None
        self.ticket.save()

        response = self.client.post(self.url, data={"action": "close_ticket"})
        self.assertRedirects(response, self.url)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.CLOSED)
        self.assertEqual(self.ticket.closed_reason, Ticket.ClosedReason.ANSWERED)
        self.assertIsNotNone(self.ticket.closed_at)
        self.assertIsNone(self.ticket.awaiting_student_since)

    def test_post_close_ticket_returns_404_for_student(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(self.url, data={"action": "close_ticket"})
        self.assertEqual(response.status_code, 404)

    def test_post_close_ticket_returns_404_for_other_staff_not_assigned(self):
        other_staff = User.objects.create_user(
            username="@otherstaff",
            email="otherstaff@example.org",
            password="Password123",
            first_name="Other",
            last_name="Staff",
            user_type=User.USER_TYPE_STAFF,
        )

        self.client.login(username=other_staff.username, password="Password123")
        response = self.client.post(self.url, data={"action": "close_ticket"})
        self.assertEqual(response.status_code, 404)

    def test_post_close_ticket_redirects_if_already_closed(self):
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.ticket.closed_at = timezone.now()
        self.ticket.awaiting_student_since = None
        self.ticket.save()

        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(self.url, data={"action": "close_ticket"})
        self.assertRedirects(response, self.url)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.CLOSED)
        self.assertEqual(self.ticket.closed_reason, Ticket.ClosedReason.ANSWERED)

    def test_staff_comment_sets_status_to_awaiting_student_and_sets_timestamp(self):
        self.client.login(username=self.staff.username, password="Password123")
        self.ticket.status = Ticket.Status.AWAITING_STAFF
        self.ticket.awaiting_student_since = None
        self.ticket.save()

        before = timezone.now()
        response = self.client.post(
            self.url, data=_valid_comment_post_data("Staff reply")
        )
        after = timezone.now()

        self.assertEqual(response.status_code, 302)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.AWAITING_STUDENT)
        self.assertIsNotNone(self.ticket.awaiting_student_since)
        self.assertTrue(before <= self.ticket.awaiting_student_since <= after)

    def test_student_comment_sets_status_to_awaiting_staff_and_clears_timestamp(self):
        # Simulate ticket currently waiting on student
        self.ticket.status = Ticket.Status.AWAITING_STUDENT
        self.ticket.awaiting_student_since = timezone.now() - timedelta(days=2)
        self.ticket.save()

        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(
            self.url, data=_valid_comment_post_data("Student reply")
        )
        self.assertEqual(response.status_code, 302)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.AWAITING_STAFF)
        self.assertIsNone(self.ticket.awaiting_student_since)

    def test_comment_does_not_change_status_if_ticket_is_closed(self):
        # Closed ticket
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.ticket.closed_at = timezone.now()
        self.ticket.awaiting_student_since = timezone.now() - timedelta(days=10)
        self.ticket.save()

        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(
            self.url, data=_valid_comment_post_data("Staff comment")
        )
        self.assertEqual(response.status_code, 302)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.CLOSED)
        self.assertEqual(self.ticket.closed_reason, Ticket.ClosedReason.ANSWERED)
        # awaiting_student_since should remain unchanged by add_comment when closed
        self.assertIsNotNone(self.ticket.closed_at)

    def test_post_unclose_ticket_as_staff_opens_ticket_as_unsolved(self):
        self.client.login(username=self.staff.username, password="Password123")

        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.ticket.closed_at = timezone.now()
        self.ticket.awaiting_student_since = timezone.now() - timedelta(days=3)
        self.ticket.save()

        response = self.client.post(self.url, data={"action": "unclose_ticket"})
        self.assertRedirects(response, self.url)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.AWAITING_STAFF)
        self.assertIsNone(self.ticket.closed_reason)
        self.assertIsNone(self.ticket.closed_at)
        self.assertIsNone(self.ticket.awaiting_student_since)

    def test_post_unclose_ticket_returns_404_for_student(self):
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.ticket.closed_at = timezone.now()
        self.ticket.save()

        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(self.url, data={"action": "unclose_ticket"})
        self.assertEqual(response.status_code, 404)

    def test_post_unclose_ticket_returns_404_for_other_staff_not_assigned(self):
        other_staff = User.objects.create_user(
            username="@otherstaff2",
            email="otherstaff2@example.org",
            password="Password123",
            first_name="Other",
            last_name="Staff",
            user_type=User.USER_TYPE_STAFF,
        )

        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.ticket.closed_at = timezone.now()
        self.ticket.save()

        self.client.login(username=other_staff.username, password="Password123")
        response = self.client.post(self.url, data={"action": "unclose_ticket"})
        self.assertEqual(response.status_code, 404)

    def test_post_unclose_ticket_redirects_if_ticket_not_closed_and_makes_no_changes(
        self,
    ):
        self.client.login(username=self.staff.username, password="Password123")

        self.ticket.status = Ticket.Status.AWAITING_STUDENT
        self.ticket.closed_reason = None
        self.ticket.closed_at = None
        self.ticket.awaiting_student_since = timezone.now() - timedelta(days=2)
        self.ticket.save()

        before_status = self.ticket.status
        before_closed_reason = self.ticket.closed_reason
        before_closed_at = self.ticket.closed_at
        before_awaiting_since = self.ticket.awaiting_student_since

        response = self.client.post(self.url, data={"action": "unclose_ticket"})
        self.assertRedirects(response, self.url)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, before_status)
        self.assertEqual(self.ticket.closed_reason, before_closed_reason)
        self.assertEqual(self.ticket.closed_at, before_closed_at)
        self.assertEqual(self.ticket.awaiting_student_since, before_awaiting_since)

    def test_student_comment_on_closed_ticket_reopens_and_clears_closed_fields(self):
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.ticket.closed_at = timezone.now()
        self.ticket.awaiting_student_since = timezone.now() - timedelta(days=10)
        self.ticket.save()

        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(
            self.url,
            data=_valid_comment_post_data("Student follow-up on closed ticket"),
        )
        self.assertEqual(response.status_code, 302)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.AWAITING_STAFF)
        self.assertIsNone(self.ticket.closed_reason)
        self.assertIsNone(self.ticket.closed_at)
        self.assertIsNone(self.ticket.awaiting_student_since)

    def test_edit_ticket_fields_as_staff(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertIn("ticket_fields_form", response.context)
        form = response.context["ticket_fields_form"]
        self.assertIsInstance(form, TicketFieldsForm)
        self.assertEqual(form.instance, self.ticket)

    def test_fields_form_in_context_for_staff(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertIn("ticket_fields_form", response.context)
        self.assertIsInstance(response.context["ticket_fields_form"], TicketFieldsForm)

    def test_fields_form_not_in_context_for_non_staff(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertIsNone(response.context.get("ticket_fields_form"))

    def test_post_set_fields_as_non_staff(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(
            self.url,
            data={
                "action": "set_ticket_fields",
                "faculty": Ticket.Faculty.KBS,
                "study_level": Ticket.StudyLevel.POSTGRADUATE_RESEARCH,
                "category": Ticket.Category.WELFARE,
            },
        )
        self.ticket.refresh_from_db()
        self.assertEqual(response.status_code, 404)

    def test_post_invalid_fields(self):
        self.client.login(username=self.staff.username, password="Password123")
        initial_faculty = self.ticket.faculty
        initial_study_level = self.ticket.study_level
        initial_category = self.ticket.category
        response = self.client.post(
            self.url,
            data={
                "action": "set_ticket_fields",
                "faculty": "invalid_faculty",
                "study_level": "invalid_study_level",
                "category": "invalid_category",
            },
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.faculty, initial_faculty)
        self.assertEqual(self.ticket.study_level, initial_study_level)
        self.assertEqual(self.ticket.category, initial_category)
        self.assertEqual(response.status_code, 302)

    def test_edit_fields_as_unassigned_staff_raises_404(self):
        assigned_staff = User.objects.create_user(
            username="@assignedstaff",
            email="assignedstaff@example.org",  # Unique email
            password="Password123",
            user_type=User.USER_TYPE_STAFF,
        )
        other_staff = User.objects.create_user(
            username="@otherstaff",
            email="otherstaff@example.org",  # Unique email
            password="Password123",
            user_type=User.USER_TYPE_STAFF,
        )
        self.ticket.assigned_to = assigned_staff
        self.ticket.save()
        self.client.login(username=other_staff.username, password="Password123")
        response = self.client.post(
            self.ticket.get_absolute_url(),
            data={
                "action": "set_ticket_fields",
                "faculty": Ticket.Faculty.KBS,
                "study_level": Ticket.StudyLevel.POSTGRADUATE_RESEARCH,
                "category": Ticket.Category.WELFARE,
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_edit_fields_as_assigned_staff_success(self):
        self.client.login(
            username=self.ticket.assigned_to.username, password="Password123"
        )
        response = self.client.post(
            self.ticket.get_absolute_url(),
            data={
                "action": "set_ticket_fields",
                "faculty": Ticket.Faculty.KBS,
                "study_level": Ticket.StudyLevel.POSTGRADUATE_RESEARCH,
                "category": Ticket.Category.WELFARE,
            },
        )
        self.ticket.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.ticket.faculty, Ticket.Faculty.KBS)
