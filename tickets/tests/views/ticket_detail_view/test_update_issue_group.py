"""Tests for the ticket detail view for changing issue group field."""

from django.test import TestCase
from tickets.forms import TicketIssueGroupForm
from tickets.models import Ticket, User, IssueGroup
from tickets.tests.helpers import MenuTesterMixin

from django.utils import timezone


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
        self.issue_group = IssueGroup.objects.create(name="Test Issue Group")
        self.url = self.ticket.get_absolute_url()

    def test_post_set_issue_group_as_non_staff(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(
            self.url,
            data={"action": "set_issue_group", "issue_group": self.issue_group},
        )
        self.assertEqual(response.status_code, 404)

    def test_issue_group_in_context_for_staff(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertIn("ticket_issue_group_form", response.context)
        self.assertIsInstance(
            response.context["ticket_issue_group_form"], TicketIssueGroupForm
        )

    def test_issue_group_form_not_in_context_for_non_staff(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertIsNone(response.context.get("ticket_issue_group_form"))

    def test_post_set_issue_group_on_closed_ticket(self):
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.ticket.closed_at = timezone.now()
        self.ticket.save()
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(
            self.url,
            data={"action": "set_issue_group", "issue_group": self.issue_group},
        )
        self.assertEqual(response.status_code, 404)

    def test_post_invalid_issue_group(self):
        self.client.login(username=self.staff.username, password="Password123")
        initial_issue_group = self.ticket.issue_group
        response = self.client.post(
            self.url,
            data={"action": "set_issue_group", "issue_group": "invalid"},
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.issue_group, initial_issue_group)
        self.assertEqual(response.status_code, 302)

    def test_post_valid_issue_group(self):
        issue_group2 = IssueGroup.objects.create(name="Test Issue Group2")
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(
            self.url,
            data={"action": "set_issue_group", "issue_group": issue_group2.pk},
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.issue_group, issue_group2)
        self.assertEqual(response.status_code, 302)
