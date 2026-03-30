"""Tests of dashboard searching feature."""

from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from tickets.tests.helpers import LogInTester
from tickets.models import User, Ticket


@override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=0)
class DashboardSearchingTestCase(TestCase, LogInTester):
    """Tests of the dashboard searching feature."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.url = reverse("dashboard")
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.get(username="@janedoe")

        self.ticket_data = {
            "student": self.student,
            "faculty": Ticket.Faculty.choices[1][0],
            "study_level": Ticket.StudyLevel.choices[1][0],
            "category": Ticket.Category.choices[1][0],
        }

        # Make sure staff filters include our test tickets
        self.staff.faculties = self.ticket_data["faculty"]
        self.staff.study_levels = self.ticket_data["study_level"]
        self.staff.categories = self.ticket_data["category"]
        self.staff.save()

    def test_student_using_search(self):
        self.client.login(username="@johndoe", password="Password123")
        Ticket.objects.create(
            subject="Test ticket 1", body="This is a test ticket 1.", **self.ticket_data
        )
        Ticket.objects.create(
            subject="Another test", body="This is a test ticket 2", **self.ticket_data
        )
        Ticket.objects.create(
            subject="Unrelated", body="Body for ticket 3", **self.ticket_data
        )

        response = self.client.get(self.url, {"searchTerm": "test"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 3)  # student shouldnt be able to use search

    def test_empty_search_term(self):
        self.client.login(username="@janedoe", password="Password123")
        Ticket.objects.create(
            subject="Test ticket 1", body="This is a test ticket 1.", **self.ticket_data
        )
        Ticket.objects.create(
            subject="Another test", body="This is a test ticket 2", **self.ticket_data
        )

        response = self.client.get(self.url, {"searchTerm": ""})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 2)

    def test_search_terms(self):
        self.client.login(username="@janedoe", password="Password123")
        user2 = User.objects.create_user(
            username="@alice",
            email="test@gmail.com",
            password="Password123",
            first_name="Alice",
            last_name="Smith",
        )
        ticket1 = Ticket.objects.create(
            subject="Test ticket 1", body="This is a test ticket 1.", **self.ticket_data
        )
        ticket2 = Ticket.objects.create(
            subject="Another test",
            body="This is a test ticket 2",
            faculty=Ticket.Faculty.choices[1][0],
            study_level=Ticket.StudyLevel.choices[1][0],
            category=Ticket.Category.choices[1][0],
            student=user2,
        )
        ticket3 = Ticket.objects.create(
            subject="Unrelated", body="Body for ticket 3", **self.ticket_data
        )

        # Subject testing
        response = self.client.get(self.url, {"searchTerm": "unrelated"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0], ticket3)

        # Body testing
        response = self.client.get(self.url, {"searchTerm": "test ticket 1"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0], ticket1)

        # Student username testing
        response = self.client.get(self.url, {"searchTerm": "@alice"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0], ticket2)

        # Student full name testing
        response = self.client.get(self.url, {"searchTerm": "Alice Smith"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0], ticket2)

        # Student parial name testing
        response = self.client.get(self.url, {"searchTerm": "doe"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 2)
        self.assertIn(ticket1, tickets)
        self.assertIn(ticket3, tickets)

        # No match testing
        response = self.client.get(
            self.url, {"searchTerm": "Test ticket 1, test ticket 2, unrelated"}
        )
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 0)

    def test_searching_is_case_insensitive(self):
        self.client.login(username="@janedoe", password="Password123")
        Ticket.objects.create(
            subject="Test ticket 1", body="This is a test ticket 1.", **self.ticket_data
        )

        response = self.client.get(self.url, {"searchTerm": "tEsT TiCkEt 1"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].subject, "Test ticket 1")

    def test_searching_with_whitespace(self):
        self.client.login(username="@janedoe", password="Password123")
        Ticket.objects.create(
            subject="Test ticket 1", body="This is a test ticket 1.", **self.ticket_data
        )

        response = self.client.get(self.url, {"searchTerm": "   test ticket 1   "})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].subject, "Test ticket 1")

    def test_search_term_correct_in_context(self):
        self.client.login(username="@janedoe", password="Password123")
        response = self.client.get(self.url, {"searchTerm": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["searchTerm"], "test")

    def test_search_term_preserved_between_tabs(self):
        self.client.login(username="@janedoe", password="Password123")
        response = self.client.get(
            self.url, {"searchTerm": "test", "tab": "assigned_tickets"}
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(self.url, {"tab": "open_tickets"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["searchTerm"], "test")

    def test_search_term_cleared_when_switching_to_non_dashboard_page(self):
        self.client.login(username="@janedoe", password="Password123")
        response = self.client.get(self.url, {"searchTerm": "test"})
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["searchTerm"], "")

    def test_search_with_priority_filter(self):
        self.client.login(username="@janedoe", password="Password123")
        Ticket.objects.create(
            subject="Test ticket 1",
            body="This is a test ticket 1.",
            priority=Ticket.Priority.HIGH,
            **self.ticket_data,
        )
        Ticket.objects.create(
            subject="Another test",
            body="This is a test ticket 2",
            priority=Ticket.Priority.LOW,
            **self.ticket_data,
        )
        Ticket.objects.create(
            subject="Unrelated",
            body="Body for ticket 3",
            priority=Ticket.Priority.MEDIUM,
            **self.ticket_data,
        )

        response = self.client.get(self.url, {"searchTerm": "test", "priority": "high"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].priority, Ticket.Priority.HIGH)

    def test_search_in_different_tabs(self):
        self.client.login(username="@janedoe", password="Password123")

        # Assigned ticket
        for i in range(2):
            ticket = Ticket.objects.create(
                **self.ticket_data,
                subject=f"search term {i+1}",
                body="This is a test assigned ticket.",
            )
            ticket.assigned_to.add(self.staff)

        response = self.client.get(
            self.url, {"searchTerm": "search term 1", "tab": "assigned_tickets"}
        )
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].subject, "search term 1")

        # Overdue ticket
        for i in range(2):
            ticket = Ticket.objects.create(
                **self.ticket_data,
                subject=f"search term {i+1}",
                body="This is a test overdue ticket.",
                status=Ticket.Status.AWAITING_STAFF,
            )
            Ticket.objects.filter(pk=ticket.pk).update(
                created_at=timezone.now() - timedelta(days=10)
            )

        response = self.client.get(
            self.url, {"searchTerm": "search term 1", "tab": "overdue_tickets"}
        )
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].subject, "search term 1")

        # Closed ticket
        for i in range(2):
            Ticket.objects.create(
                **self.ticket_data,
                subject=f"test closed ticket {i+1}",
                body="This is a test closed ticket.",
                status=Ticket.Status.CLOSED,
                closed_reason=Ticket.ClosedReason.ANSWERED,
                closed_at=timezone.now(),
            )

        response = self.client.get(
            self.url, {"searchTerm": "test closed ticket 1", "tab": "closed_tickets"}
        )
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].subject, "test closed ticket 1")

    def test_search_results_are_ordered_oldest_first_when_order_is_oldest(self):
        self.client.login(username="@janedoe", password="Password123")

        older_ticket = Ticket.objects.create(
            subject="Matching ticket older",
            body="search target",
            **self.ticket_data,
        )
        newer_ticket = Ticket.objects.create(
            subject="Matching ticket newer",
            body="search target",
            **self.ticket_data,
        )

        Ticket.objects.filter(pk=older_ticket.pk).update(
            created_at=timezone.now() - timedelta(days=2)
        )
        Ticket.objects.filter(pk=newer_ticket.pk).update(
            created_at=timezone.now() - timedelta(days=1)
        )

        response = self.client.get(
            self.url,
            {
                "searchTerm": "Matching ticket",
                "order": "oldest",
            },
        )

        self.assertEqual(response.status_code, 200)
        tickets = list(response.context["page_obj"].object_list)
        self.assertEqual(tickets[0].pk, older_ticket.pk)
        self.assertEqual(tickets[1].pk, newer_ticket.pk)

    def test_search_results_are_ordered_newest_first_by_default(self):
        self.client.login(username="@janedoe", password="Password123")

        older_ticket = Ticket.objects.create(
            subject="Matching ticket older",
            body="search target",
            **self.ticket_data,
        )
        newer_ticket = Ticket.objects.create(
            subject="Matching ticket newer",
            body="search target",
            **self.ticket_data,
        )

        Ticket.objects.filter(pk=older_ticket.pk).update(
            created_at=timezone.now() - timedelta(days=2)
        )
        Ticket.objects.filter(pk=newer_ticket.pk).update(
            created_at=timezone.now() - timedelta(days=1)
        )

        response = self.client.get(
            self.url,
            {
                "searchTerm": "Matching ticket",
            },
        )

        self.assertEqual(response.status_code, 200)
        tickets = list(response.context["page_obj"].object_list)
        self.assertEqual(tickets[0].pk, newer_ticket.pk)
        self.assertEqual(tickets[1].pk, older_ticket.pk)
