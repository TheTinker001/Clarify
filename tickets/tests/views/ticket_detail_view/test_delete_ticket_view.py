"""Tests for DeleteTicketView."""

from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from tickets.models import Ticket
from django.contrib.auth import get_user_model

User = get_user_model()


class DeleteTicketViewTest(TestCase):
    """Tests for DeleteTicketView."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.other_student = User.objects.get(username="@petrapickles")
        self.staff = User.objects.get(username="@janedoe")
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="To delete",
            body="Body.",
        )
        self.url = reverse("delete_ticket", kwargs={"url_code": self.ticket.url_code})

    def test_student_can_delete_within_window(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Ticket.objects.filter(pk=self.ticket.pk).count(), 0)

    @override_settings(TICKET_EDIT_WINDOW_MINUTES=10)
    def test_student_cannot_delete_after_window(self):
        Ticket.objects.filter(pk=self.ticket.pk).update(
            created_at=timezone.now() - timedelta(minutes=11)
        )
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(self.url)
        self.assertRedirects(response, self.ticket.get_absolute_url())
        self.assertEqual(Ticket.objects.filter(pk=self.ticket.pk).count(), 1)

    def test_staff_cannot_delete(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_other_student_cannot_delete(self):
        self.client.login(username=self.other_student.username, password="Password123")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_get_not_allowed(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_redirects_to_dashboard_after_delete(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("dashboard"))
