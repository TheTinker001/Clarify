"""Tests of dashboard searching feature."""

from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from tickets.models import User
from tickets.models.ticket import Ticket
from tickets.tests.helpers import LogInTester
from django.utils import timezone


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
        tickets = response.context["tickets"]
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
        tickets = response.context["tickets"]
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
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0], ticket3)

        # Body testing
        response = self.client.get(self.url, {"searchTerm": "test ticket 1"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0], ticket1)

        # Student username testing
        response = self.client.get(self.url, {"searchTerm": "@alice"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0], ticket2)

        # Student full name testing
        response = self.client.get(self.url, {"searchTerm": "Alice Smith"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0], ticket2)

        # Student parial name testing
        response = self.client.get(self.url, {"searchTerm": "doe"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets), 2)
        self.assertIn(ticket1, tickets)
        self.assertIn(ticket3, tickets)

        # No match testing
        response = self.client.get(
            self.url, {"searchTerm": "Test ticket 1, test ticket 2, unrelated"}
        )
        self.assertEqual(response.status_code, 200)
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets), 0)

    def test_searching_is_case_insensitive(self):
        self.client.login(username="@janedoe", password="Password123")
        Ticket.objects.create(
            subject="Test ticket 1", body="This is a test ticket 1.", **self.ticket_data
        )

        response = self.client.get(self.url, {"searchTerm": "tEsT TiCkEt 1"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].subject, "Test ticket 1")

    def test_searching_with_whitespace(self):
        self.client.login(username="@janedoe", password="Password123")
        Ticket.objects.create(
            subject="Test ticket 1", body="This is a test ticket 1.", **self.ticket_data
        )

        response = self.client.get(self.url, {"searchTerm": "   test ticket 1   "})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["tickets"]
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
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].priority, Ticket.Priority.HIGH)

    def test_search_in_different_tabs(self):
        self.client.login(username="@janedoe", password="Password123")
        # Assigned ticket
        for i in range(2):
            Ticket.objects.create(
                **self.ticket_data,
                subject=f"search term {i+1}",
                body="This is a test assigned ticket.",
                assigned_to=self.staff,
            )
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
            self.url, {"searchTerm": "search term 1", "tab": "assigned_tickets"}
        )
        self.assertEqual(response.status_code, 200)
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].subject, "search term 1")

        response = self.client.get(
            self.url, {"searchTerm": "search term 1", "tab": "overdue_tickets"}
        )
        self.assertEqual(response.status_code, 200)
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].subject, "search term 1")

        response = self.client.get(
            self.url, {"searchTerm": "test closed ticket 1", "tab": "closed_tickets"}
        )
        self.assertEqual(response.status_code, 200)
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].subject, "test closed ticket 1")


class DashboardFilteringTestCase(TestCase, LogInTester):
    """Tests of the dashboard filtering feature."""

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
        self.create_tickets_with_various_attributes()

    def create_tickets_with_various_attributes(self):
        for i in range(3):
            Ticket.objects.create(
                subject=f"Test ticket {i+1}",
                body="This is a test ticket.",
                priority=Ticket.Priority.HIGH,
                **self.ticket_data,
            )
        self.ticket = Ticket.objects.create(
            subject="Another test",
            body="This is another test ticket.",
            priority=Ticket.Priority.HIGH,
            student=self.student,
            faculty=Ticket.Faculty.AH,
            study_level=Ticket.StudyLevel.OTHER,
            category=Ticket.Category.WELFARE,
        )

    def test_student_cannot_access_filtering(self):
        self.client.login(username="@johndoe", password="Password123")
        response = self.client.get(
            self.url,
            {
                "priority": "high",
                "faculty": Ticket.Faculty.AH,
                "study_level": Ticket.StudyLevel.OTHER,
                "category": Ticket.Category.WELFARE,
            },
        )
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), 4)
        # student shouldnt be able to use filters, so all 4 tickets should be returned

    def test_filtering_with_invalid_inputs(self):
        self.client.login(username="@janedoe", password="Password123")
        Ticket.objects.create(
            status=Ticket.Status.AWAITING_STAFF,
            assigned_to=None,
            subject="Test ticket 1",
            body="This is a test ticket 1.",
            **self.ticket_data,
        )
        Ticket.objects.create(
            status=Ticket.Status.AWAITING_STAFF,
            assigned_to=None,
            subject="Test ticket 2",
            body="This is a test ticket 2.",
            **self.ticket_data,
        )

        base_params = {"tab": "open_tickets"}
        baseline_response = self.client.get(self.url, base_params)
        self.assertEqual(baseline_response.status_code, 200)
        baseline_count = baseline_response.context["tickets"].paginator.count

        invalid_cases = [
            ("faculty", "NOT_A_REAL_FACULTY"),
            ("study_level", "NOT_A_REAL_LEVEL"),
            ("category", "NOT_A_REAL_CATEGORY"),
        ]

        for field, bad_value in invalid_cases:
            with self.subTest(field=field):
                params = {**base_params, field: bad_value}
                response = self.client.get(self.url, params)
                self.assertEqual(response.status_code, 200)

                count = response.context["tickets"].paginator.count
                self.assertEqual(count, baseline_count)

    def test_individual_filters(self):
        self.client.login(username="@janedoe", password="Password123")

        cases = [
            ("faculty", Ticket.Faculty.AH),
            ("study_level", Ticket.StudyLevel.OTHER),
            ("category", Ticket.Category.WELFARE),
        ]

        for field, bad_value in cases:
            with self.subTest(field=field):
                response = self.client.get(self.url, {field: bad_value})
                self.assertEqual(response.status_code, 200)
                tickets = response.context["page_obj"].object_list
                self.assertEqual(len(tickets), 1)
                self.assertEqual(tickets[0], self.ticket)

    def test_combined_filters(self):
        self.client.login(username="@janedoe", password="Password123")

        t_match = Ticket.objects.create(
            subject="Matching ticket subject",
            body="Matching ticket body",
            faculty=Ticket.Faculty.NMES,
            study_level=Ticket.StudyLevel.POSTGRADUATE_RESEARCH,
            category=Ticket.Category.UNI_PROCEDURES_REGULATIONS,
            student=self.student,
        )

        Ticket.objects.create(
            subject="Wrong faculty",
            body="Wrong faculty",
            faculty=Ticket.Faculty.AH,
            study_level=Ticket.StudyLevel.POSTGRADUATE_RESEARCH,
            category=Ticket.Category.UNI_PROCEDURES_REGULATIONS,
            student=self.student,
        )

        # Wrong category + study level
        Ticket.objects.create(
            subject="Wrong category and study level",
            body="Wrong category and study level",
            faculty=Ticket.Faculty.NMES,
            study_level=Ticket.StudyLevel.OTHER,
            category=Ticket.Category.WELFARE,
            student=self.student,
        )

        response = self.client.get(
            self.url,
            {
                "faculty": Ticket.Faculty.NMES,
                "study_level": Ticket.StudyLevel.POSTGRADUATE_RESEARCH,
                "category": Ticket.Category.UNI_PROCEDURES_REGULATIONS,
            },
        )
        self.assertEqual(response.status_code, 200)
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0], t_match)

    def test_filter_with_search(self):
        self.client.login(username="@janedoe", password="Password123")

        t_match = Ticket.objects.create(
            subject="Matching ticket subject",
            body="Matching ticket body",
            faculty=Ticket.Faculty.NMES,
            study_level=Ticket.StudyLevel.POSTGRADUATE_RESEARCH,
            category=Ticket.Category.UNI_PROCEDURES_REGULATIONS,
            student=self.student,
        )

        Ticket.objects.create(
            subject="Extra ticket subject",
            body="Extra ticket body",
            faculty=Ticket.Faculty.NMES,
            study_level=Ticket.StudyLevel.POSTGRADUATE_RESEARCH,
            category=Ticket.Category.UNI_PROCEDURES_REGULATIONS,
            student=self.student,
        )

        response = self.client.get(
            self.url,
            {
                "faculty": Ticket.Faculty.NMES,
                "study_level": Ticket.StudyLevel.POSTGRADUATE_RESEARCH,
                "category": Ticket.Category.UNI_PROCEDURES_REGULATIONS,
                "searchTerm": "matching ticket subject",
            },
        )
        self.assertEqual(response.status_code, 200)
        tickets = response.context["tickets"]
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0], t_match)
