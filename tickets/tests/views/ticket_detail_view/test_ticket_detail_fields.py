"""Tests for the ticket detail view."""

from django.test import TestCase, override_settings
from tickets.forms import TicketFieldsForm
from tickets.models import Ticket, User
from tickets.tests.helpers import MenuTesterMixin
from tickets.views import TicketDetailView


@override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=0)
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
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Update card access",
            body="Card access not working for lab.",
        )
        self.ticket.assigned_to.add(self.staff)
        self.url = self.ticket.get_absolute_url()
        self.admin = User.objects.create_user(
            username="@adminstaff",
            email="adminstaff@example.org",
            password="Password123",
            user_type=User.USER_TYPE_STAFF,
            is_staff=True,
            is_superuser=True,
        )

    def test_fields_form_in_context_for_admin(self):
        self.client.login(username=self.admin.username, password="Password123")
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
        self.client.login(username=self.admin.username, password="Password123")
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
        self.ticket.assigned_to.add(assigned_staff)
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

    def test_edit_fields_as_admin_success(self):
        self.client.login(username=self.admin.username, password="Password123")
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

    def test_get_fields_form_returns_none_for_non_staff(self):
        view = TicketDetailView()
        view.ticket = self.ticket
        view.is_staff_user = False  # Simulate non-staff user
        form = view.get_fields_form()
        self.assertIsNone(form)

    def test_edit_ticket_fields_as_admin(self):
        self.client.login(username=self.admin.username, password="Password123")
        response = self.client.get(self.url)
        self.assertIn("ticket_fields_form", response.context)
        form = response.context["ticket_fields_form"]
        self.assertIsInstance(form, TicketFieldsForm)
        self.assertEqual(form.instance, self.ticket)

    def test_fields_form_not_in_context_for_staff(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertIsNone(response.context.get("ticket_fields_form"))
