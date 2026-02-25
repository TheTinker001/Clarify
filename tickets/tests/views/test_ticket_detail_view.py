"""Tests for the ticket detail view."""

from django.urls import reverse
from django.utils import timezone
from django.test import TestCase
from tickets.forms.ticket_priority_form import TicketPriorityForm
from tickets.models import Ticket, User
from tickets.tests.helpers import MenuTesterMixin, reverse_with_next


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
