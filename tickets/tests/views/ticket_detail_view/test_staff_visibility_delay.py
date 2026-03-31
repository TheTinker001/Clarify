"""Tests for staff being able to view student tickets after 15 minutes."""

from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from tickets.models import Ticket
from django.contrib.auth import get_user_model

User = get_user_model()


class StaffVisibilityDelayTest(TestCase):
    """Tests for staff being able to view student tickets after 15 minutes."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.get(username="@janedoe")
        self.staff.faculties = "kbs"
        self.staff.study_levels = "undergraduate"
        self.staff.categories = "other"
        self.staff.save(update_fields=["faculties", "study_levels", "categories"])

        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="New ticket",
            body="Body.",
        )

    @override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=15)
    def test_staff_cannot_view_ticket_before_15_minutes(self):
        self.client.login(username=self.staff.username, password="Password123")
        url = self.ticket.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=15)
    def test_staff_can_view_ticket_after_15_minutes(self):
        Ticket.objects.filter(pk=self.ticket.pk).update(
            created_at=timezone.now() - timedelta(minutes=16)
        )
        self.client.login(username=self.staff.username, password="Password123")
        url = self.ticket.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_student_can_always_view_own_ticket(self):
        self.client.login(username=self.student.username, password="Password123")
        url = self.ticket.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=15)
    def test_staff_dashboard_hides_new_tickets(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(reverse("dashboard"), {"tab": "open_tickets"})
        self.assertEqual(response.status_code, 200)
        tickets_shown = response.context["page_obj"].object_list
        self.assertEqual(len(tickets_shown), 0)

    @override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=15)
    def test_staff_dashboard_shows_old_tickets(self):
        Ticket.objects.filter(pk=self.ticket.pk).update(
            created_at=timezone.now() - timedelta(minutes=16)
        )
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(reverse("dashboard"), {"tab": "open_tickets"})
        self.assertEqual(response.status_code, 200)
        tickets_shown = response.context["page_obj"].object_list
        self.assertEqual(len(tickets_shown), 1)
