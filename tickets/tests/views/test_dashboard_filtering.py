"""Tests of the dashboard filtering feature."""

from django.test import TestCase
from django.urls import reverse
from tickets.models import User
from tickets.models.ticket import Ticket
from tickets.tests.helpers import LogInTester


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
