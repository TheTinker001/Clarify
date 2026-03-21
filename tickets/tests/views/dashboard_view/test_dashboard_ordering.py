"""Tests for the ticket age (time ordering) filter on the staff dashboard."""

from django.test import TestCase
from django.urls import reverse
from tickets.models import User
from tickets.models.ticket import Ticket
from tickets.tests.helpers import LogInTester


class DashboardOrderingTestCase(TestCase, LogInTester):
    """Tests for the ticket age ordering filter on the staff dashboard."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.url = reverse("dashboard")
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.get(username="@janedoe")

        faculty = Ticket.Faculty.choices[1][0]
        study_level = Ticket.StudyLevel.choices[1][0]
        category = Ticket.Category.choices[1][0]

        self.staff.faculties = faculty
        self.staff.study_levels = study_level
        self.staff.categories = category
        self.staff.save()

        self.ticket_data = {
            "student": self.student,
            "faculty": faculty,
            "study_level": study_level,
            "category": category,
            "status": Ticket.Status.AWAITING_STAFF,
        }

        self.ticket_old = Ticket.objects.create(
            subject="Old ticket",
            body="Old ticket body.",
            **self.ticket_data,
        )
        self.ticket_new = Ticket.objects.create(
            subject="New ticket",
            body="New ticket body.",
            **self.ticket_data,
        )

    def test_default_ordering_is_newest_first(self):
        """Staff dashboard defaults to newest-first ordering."""
        self.client.login(username="@janedoe", password="Password123")
        response = self.client.get(self.url, {"tab": "open_tickets"})
        self.assertEqual(response.status_code, 200)
        tickets = list(response.context["page_obj"].object_list)
        self.assertEqual(tickets[0], self.ticket_new)
        self.assertEqual(tickets[1], self.ticket_old)

    def test_explicit_newest_ordering(self):
        """Passing order=newest returns tickets newest first."""
        self.client.login(username="@janedoe", password="Password123")
        response = self.client.get(self.url, {"tab": "open_tickets", "order": "newest"})
        self.assertEqual(response.status_code, 200)
        tickets = list(response.context["page_obj"].object_list)
        self.assertEqual(tickets[0], self.ticket_new)
        self.assertEqual(tickets[1], self.ticket_old)

    def test_oldest_ordering(self):
        """Passing order=oldest returns tickets oldest first."""
        self.client.login(username="@janedoe", password="Password123")
        response = self.client.get(self.url, {"tab": "open_tickets", "order": "oldest"})
        self.assertEqual(response.status_code, 200)
        tickets = list(response.context["page_obj"].object_list)
        self.assertEqual(tickets[0], self.ticket_old)
        self.assertEqual(tickets[1], self.ticket_new)

    def test_invalid_order_value_falls_back_to_newest(self):
        """An invalid order param defaults to newest-first."""
        self.client.login(username="@janedoe", password="Password123")
        response = self.client.get(
            self.url, {"tab": "open_tickets", "order": "invalid"}
        )
        self.assertEqual(response.status_code, 200)
        tickets = list(response.context["page_obj"].object_list)
        self.assertEqual(tickets[0], self.ticket_new)
        self.assertEqual(tickets[1], self.ticket_old)

    def test_student_ordering_unaffected_by_order_param(self):
        """Students are not affected by the order param; their tickets use default ordering."""
        self.client.login(username="@johndoe", password="Password123")
        response = self.client.get(self.url, {"tab": "open_tickets", "order": "oldest"})
        self.assertEqual(response.status_code, 200)
        tickets = list(response.context["page_obj"].object_list)
        self.assertEqual(tickets[0], self.ticket_new)
        self.assertEqual(tickets[1], self.ticket_old)

    def test_order_filter_in_context(self):
        """The order value is present in the context filters dict."""
        self.client.login(username="@janedoe", password="Password123")
        response = self.client.get(self.url, {"tab": "open_tickets", "order": "oldest"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["filters"]["order"], "oldest")

    def test_order_default_in_context_when_not_specified(self):
        """When order param is absent, context filters.order defaults to 'newest'."""
        self.client.login(username="@janedoe", password="Password123")
        response = self.client.get(self.url, {"tab": "open_tickets"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["filters"]["order"], "newest")
