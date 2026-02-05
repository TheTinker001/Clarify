"""Tests for the ticket detail view."""

from django.test import TestCase
from django.urls import reverse
from tickets.models import Ticket, User
from tickets.tests.helpers import MenuTesterMixin, reverse_with_next


class TicketDetailViewTestCase(TestCase, MenuTesterMixin):
    """Test suite for the ticket detail view."""

    fixtures = ["tickets/tests/fixtures/default_user.json"]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
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
        self.url = reverse("ticket_detail", kwargs={"pk": self.ticket.pk})

    def test_ticket_detail_url(self):
        self.assertEqual(self.url, f"/ticket/{self.ticket.pk}/")

    def test_get_ticket_detail_redirects_when_not_logged_in(self):
        redirect_url = reverse_with_next("log_in", self.url)
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
        response = self.client.get("/ticket/9999/")
        self.assertEqual(response.status_code, 404)
