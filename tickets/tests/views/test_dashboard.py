"""Tests of dashboard view."""

from datetime import timedelta
from django.contrib.auth.hashers import check_password
from django.test import TestCase
from django.urls import reverse
from clarify import settings
from tickets.models import User
from tickets.models.ticket import Ticket
from tickets.tests.helpers import LogInTester
from django.utils import timezone


class DashboardViewTestCase(TestCase, LogInTester):
    """Tests of the dashboard view."""

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
            "body": "This is a test ticket body.",
        }
        self.staff.faculties = self.ticket_data["faculty"]
        self.staff.study_levels = self.ticket_data["study_level"]
        self.staff.categories = self.ticket_data["category"]
        self.staff.save()

    def test_home_url(self):
        self.assertEqual(self.url, "/dashboard/")

    def test_get_dashboard_when_logged_in(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")

    def test_get_dashboard_redirects_when_not_logged_in(self):
        response = self.client.get(self.url, follow=True)
        redirect_url = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertTemplateUsed(response, "log_in.html")

    def test_pagination_on_dashboard(self):
        self.client.login(username=self.student.username, password="Password123")
        for i in range(30):
            Ticket.objects.create(**self.ticket_data, subject=f"Test ticket {i+1}")

        response = self.client.get(self.url, {"tab": "open_tickets", "page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn("page_obj", response.context)

        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.paginator.per_page, settings.ITEMS_PER_PAGE)
        self.assertEqual(page_obj.start_index(), 1)
        self.assertEqual(page_obj.end_index(), min(settings.ITEMS_PER_PAGE, 30))
        self.assertEqual(len(page_obj.object_list), min(settings.ITEMS_PER_PAGE, 30))

        response2 = self.client.get(self.url, {"tab": "open_tickets", "page": 2})
        self.assertEqual(response2.status_code, 200)
        page_obj2 = response2.context["page_obj"]
        self.assertEqual(len(page_obj2.object_list), 10)

    def test_context_when_user_is_staff(self):
        self.client.login(username=self.staff.username, password="Password123")
        # create 6 open tickets
        for i in range(6):
            Ticket.objects.create(**self.ticket_data, subject=f"Test open ticket {i+1}")
        # create 3 assigned tickets
        for i in range(3):
            Ticket.objects.create(
                **self.ticket_data,
                subject=f"Test assigned ticket {i+1}",
                assigned_to=self.staff,
            )
        # create 4 overdue tickets
        for i in range(4):
            ticket = Ticket.objects.create(
                **self.ticket_data,
                subject=f"Test overdue ticket {i+1}",
                status=Ticket.Status.AWAITING_STAFF,
            )

            Ticket.objects.filter(pk=ticket.pk).update(
                created_at=timezone.now() - timedelta(days=10)
            )
        # create 5 closed tickets
        for i in range(5):
            Ticket.objects.create(
                **self.ticket_data,
                subject=f"Test closed ticket {i+1}",
                status=Ticket.Status.CLOSED,
                closed_reason=Ticket.ClosedReason.ANSWERED,
                closed_at=timezone.now(),
            )

        self.client.login(username=self.staff.username, password="Password123")

        resp = self.client.get(self.url, {"tab": "open_tickets", "page": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["page_obj"].object_list), 6)

        resp = self.client.get(self.url, {"tab": "assigned_tickets", "page": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["page_obj"].object_list), 3)

        resp = self.client.get(self.url, {"tab": "overdue_tickets", "page": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["page_obj"].object_list), 4)

        resp = self.client.get(self.url, {"tab": "closed_tickets", "page": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["page_obj"].object_list), 5)

    def test_context_when_user_is_student(self):
        self.client.login(username=self.student.username, password="Password123")

        # 4 open
        for i in range(4):
            Ticket.objects.create(
                **self.ticket_data,
                subject=f"Test open ticket {i+1}",
                status=Ticket.Status.AWAITING_STAFF,
                assigned_to=None,
            )
        # 3 in progress
        for i in range(3):
            Ticket.objects.create(
                **self.ticket_data,
                subject=f"Test assigned ticket {i+1}",
                status=Ticket.Status.AWAITING_STAFF,
                assigned_to=self.staff,
            )
        # 2 need response
        for i in range(2):
            Ticket.objects.create(
                **self.ticket_data,
                subject=f"Test need response ticket {i+1}",
                status=Ticket.Status.AWAITING_STUDENT,
            )
        # 5 closed
        for i in range(5):
            Ticket.objects.create(
                **self.ticket_data,
                subject=f"Closed ticket {i+1}",
                status=Ticket.Status.CLOSED,
                closed_reason=Ticket.ClosedReason.ANSWERED,
                closed_at=timezone.now(),
            )

        self.client.login(username=self.student.username, password="Password123")

        resp = self.client.get(self.url, {"tab": "open_tickets", "page": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["page_obj"].object_list), 4)

        resp = self.client.get(self.url, {"tab": "in_progress_tickets", "page": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["page_obj"].object_list), 3)

        resp = self.client.get(self.url, {"tab": "need_response_tickets", "page": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["page_obj"].object_list), 2)

        resp = self.client.get(self.url, {"tab": "closed_tickets", "page": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["page_obj"].object_list), 5)

    def test_dashboard_invalid_tab_defaults_to_open(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url, {"tab": "not_a_real_tab"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tab"], "open_tickets")
        self.assertEqual(response.context["category"], "Open")

    def test_dashboard_unknown_user_type_does_not_crash(self):
        weird_user = User.objects.create_user(
            first_name="Weird",
            last_name="User",
            username="@weirduser",
            email="weirduser@example.org",
            user_type=User.USER_TYPE_STUDENT,  # create valid first
            password="Password123",
        )
        # Force an invalid user_type value
        User.objects.filter(pk=weird_user.pk).update(user_type="UNKNOWN")

        self.client.login(username=weird_user.username, password="Password123")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["tab"], "open_tickets")
        self.assertEqual(len(resp.context["page_obj"].object_list), 0)

    def test_ticket_card_contains_link_to_ticket_detail(self):
        self.client.login(username=self.student.username, password="Password123")
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test subject",
            body="Test body",
        )

        response = self.client.get(self.url, {"tab": "open_tickets", "page": 1})
        self.assertEqual(response.status_code, 200)
        detail_url = ticket.get_absolute_url()
        self.assertContains(response, f'href="{detail_url}"')
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, 200)

    def test_dashboard_priority_sorting(self):
        self.client.login(username=self.staff.username, password="Password123")
        priorities = [
            Ticket.Priority.HIGH,
            Ticket.Priority.MEDIUM,
            Ticket.Priority.LOW,
            Ticket.Priority.PENDING_PRIORITY,
        ]
        for i in priorities:
            Ticket.objects.create(
                **self.ticket_data,
                subject=f"Test ticket {i}",
                priority=i,
            )

        response = self.client.get(self.url, {"tab": "open_tickets", "sort": "high"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertTrue(all(t.priority == Ticket.Priority.HIGH for t in tickets))

        response = self.client.get(self.url, {"tab": "open_tickets", "sort": "medium"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertTrue(all(t.priority == Ticket.Priority.MEDIUM for t in tickets))

        response = self.client.get(self.url, {"tab": "open_tickets", "sort": "low"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertTrue(all(t.priority == Ticket.Priority.LOW for t in tickets))

        response = self.client.get(self.url, {"tab": "open_tickets", "sort": "pending"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertTrue(
            all(t.priority == Ticket.Priority.PENDING_PRIORITY for t in tickets)
        )

        response = self.client.get(self.url, {"tab": "open_tickets", "sort": "invalid"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), len(Ticket.objects.all()))

    def test_student_dashboard_priority_sorting(self):
        self.client.login(username=self.student.username, password="Password123")
        priorities = [
            Ticket.Priority.HIGH,
            Ticket.Priority.MEDIUM,
            Ticket.Priority.LOW,
            Ticket.Priority.PENDING_PRIORITY,
        ]
        for i in priorities:
            Ticket.objects.create(
                **self.ticket_data,
                subject=f"Test ticket {i}",
                priority=i,
            )

        # Returns all without sorting since students don't have sorting options
        response = self.client.get(self.url, {"tab": "open_tickets", "sort": "high"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), len(Ticket.objects.all()))

        response = self.client.get(self.url, {"tab": "open_tickets", "sort": "medium"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), len(Ticket.objects.all()))

        response = self.client.get(self.url, {"tab": "open_tickets", "sort": "low"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), len(Ticket.objects.all()))

        response = self.client.get(self.url, {"tab": "open_tickets", "sort": "pending"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), len(Ticket.objects.all()))

        response = self.client.get(self.url, {"tab": "open_tickets", "sort": "invalid"})
        self.assertEqual(response.status_code, 200)
        tickets = response.context["page_obj"].object_list
        self.assertEqual(len(tickets), len(Ticket.objects.all()))

    def test_dashboard_tab_not_in_groups_defaults_to_open_for_staff(self):
        self.client.login(username=self.staff.username, password="Password123")

        # Create 2 "open" tickets for staff (unassigned, awaiting staff, not overdue)
        for i in range(2):
            Ticket.objects.create(
                **self.ticket_data,
                subject=f"Open {i+1}",
                status=Ticket.Status.AWAITING_STAFF,
                assigned_to=None,
            )

        # Ticket not in open_tickets
        Ticket.objects.create(
            **self.ticket_data,
            subject="Assigned",
            status=Ticket.Status.AWAITING_STAFF,
            assigned_to=self.staff,
        )

        # This tab is valid in TAB_LABELS but doesn't exist in staff groups
        response = self.client.get(self.url, {"tab": "in_progress_tickets"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tab"], "open_tickets")
        self.assertEqual(response.context["category"], "Open")
        self.assertEqual(len(response.context["page_obj"].object_list), 2)

    def test_staff_with_multiple_comma_separated_preferences(self):
        self.staff.faculties = "folsm,sspp"
        self.staff.study_levels = "undergraduate,postgraduate_taught"
        self.staff.categories = "assessment,health_and_wellbeing"
        self.staff.save()
        # Create tickets for each combination
        Ticket.objects.create(
            student=self.student,
            faculty="folsm",
            study_level="undergraduate",
            category="assessment",
            subject="Test1",
            body="Test",
        )
        Ticket.objects.create(
            student=self.student,
            faculty="sspp",
            study_level="postgraduate_taught",
            category="health_and_wellbeing",
            subject="Test2",
            body="Test",
        )
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Should find both tickets
        self.assertGreaterEqual(len(response.context["page_obj"].object_list), 2)
