"""Tests for the ticket claim view."""

from django.test import TestCase
from tickets.models import Ticket, User
from tickets.tests.helpers import MenuTesterMixin


class TicketClaimTestCase(TestCase, MenuTesterMixin):
    """Test suite for the ticket claim view."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

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
        self.url = self.ticket.get_absolute_url()

    def test_ticket_claim_and_unclaim(self):
        self.client.login(username=self.staff.username, password="Password123")
        claim_url = self.ticket.get_claim_url()
        response = self.client.post(claim_url, follow=True)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.staff)
        self.assertContains(response, "You have claimed this ticket.")

        unclaim_url = self.ticket.get_unclaim_url()
        response = self.client.post(unclaim_url, follow=True)

        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.assigned_to)
        self.assertContains(response, "You have unclaimed this ticket.")

    def test_ticket_claim_and_unclaim_by_non_staff(self):
        self.client.login(username=self.student.username, password="Password123")
        claim_url = self.ticket.get_claim_url()
        response = self.client.post(claim_url, follow=True)
        self.ticket.refresh_from_db()
        self.assertNotEqual(self.ticket.assigned_to, self.student)
        self.assertContains(response, "You are not a staff member!")

        unclaim_url = self.ticket.get_unclaim_url()
        response = self.client.post(unclaim_url, follow=True)
        self.ticket.refresh_from_db()
        self.assertNotEqual(self.ticket.assigned_to, self.student)
        self.assertContains(response, "You are not a staff member!")

    def test_ticket_claim_already_claimed(self):
        other_staff = User.objects.create_user(
            username="@otherstaff",
            password="Password123",
            user_type=User.USER_TYPE_STAFF,
        )
        self.ticket.assigned_to = other_staff
        self.ticket.save()
        self.client.login(username=self.staff.username, password="Password123")
        claim_url = self.ticket.get_claim_url()
        response = self.client.post(claim_url, follow=True)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, other_staff)
        self.assertContains(response, f"Ticket already claimed by {other_staff}.")

    def test_ticket_unclaim_not_assigned(self):
        other_staff = User.objects.create_user(
            username="@otherstaff",
            password="Password123",
            user_type=User.USER_TYPE_STAFF,
        )
        self.ticket.assigned_to = other_staff
        self.ticket.save()
        self.client.login(username=self.staff.username, password="Password123")
        unclaim_url = self.ticket.get_unclaim_url()
        response = self.client.post(unclaim_url, follow=True)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, other_staff)
        self.assertContains(response, f"You are not assigned to this ticket.")

    def test_ticket_claim_unclaimed(self):
        self.ticket.assigned_to = None
        self.ticket.save(update_fields=["assigned_to"])

        self.client.login(username=self.staff.username, password="Password123")
        claim_url = self.ticket.get_claim_url()
        response = self.client.post(claim_url, follow=True)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.staff)
        self.assertContains(response, "You have claimed this ticket.")
