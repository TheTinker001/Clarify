"""Tests for the ticket claim view."""

from django.test import TestCase, override_settings
from tickets.models import Ticket, User
from tickets.tests.helpers import MenuTesterMixin


@override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=0)
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
        self.assertEqual(self.ticket.assigned_to.first(), self.staff)
        self.assertContains(response, "You have claimed this ticket.")

        unclaim_url = self.ticket.get_unclaim_url()
        response = self.client.post(unclaim_url, follow=True)

        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.assigned_to.filter(id=self.staff.id).exists())
        self.assertContains(response, "You have unclaimed this ticket.")

    def test_ticket_claim_and_unclaim_by_non_staff(self):
        self.client.login(username=self.student.username, password="Password123")
        claim_url = self.ticket.get_claim_url()
        response = self.client.post(claim_url, follow=True)
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.assigned_to.filter(id=self.student.id).exists())
        self.assertContains(response, "You are not a staff member!")

        unclaim_url = self.ticket.get_unclaim_url()
        response = self.client.post(unclaim_url, follow=True)
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.assigned_to.filter(id=self.student.id).exists())
        self.assertContains(response, "You are not a staff member!")

    def test_ticket_claim_already_claimed_by_five_staff(self):
        self.ticket.assigned_to.clear()
        self.assertEqual(self.ticket.assigned_to.count(), 0)

        other_staff1 = User.objects.create_user(
            username="@otherstaff1",
            password="Password123",
            email="otherstaff1@example.com",
            user_type=User.USER_TYPE_STAFF,
        )
        other_staff2 = User.objects.create_user(
            username="@otherstaff2",
            password="Password123",
            email="otherstaff2@example.com",
            user_type=User.USER_TYPE_STAFF,
        )
        other_staff3 = User.objects.create_user(
            username="@otherstaff3",
            password="Password123",
            email="otherstaff3@example.com",
            user_type=User.USER_TYPE_STAFF,
        )
        other_staff4 = User.objects.create_user(
            username="@otherstaff4",
            password="Password123",
            email="otherstaff4@example.com",
            user_type=User.USER_TYPE_STAFF,
        )
        other_staff5 = User.objects.create_user(
            username="@otherstaff5",
            password="Password123",
            email="otherstaff5@example.com",
            user_type=User.USER_TYPE_STAFF,
        )
        self.ticket.assigned_to.add(
            other_staff1, other_staff2, other_staff3, other_staff4, other_staff5
        )
        self.client.login(username=self.staff.username, password="Password123")
        claim_url = self.ticket.get_claim_url()
        response = self.client.post(claim_url, follow=True)
        self.ticket.refresh_from_db()
        self.assertSetEqual(
            set(self.ticket.assigned_to.all()),
            {other_staff1, other_staff2, other_staff3, other_staff4, other_staff5},
        )
        self.assertContains(
            response, "Ticket already has the maximum number of staff assigned"
        )

    def test_ticket_unclaim_not_assigned(self):
        self.ticket.assigned_to.clear()
        self.assertEqual(self.ticket.assigned_to.count(), 0)
        self.client.login(username=self.staff.username, password="Password123")
        unclaim_url = self.ticket.get_unclaim_url()
        response = self.client.post(unclaim_url, follow=True)
        self.assertContains(response, f"You are not assigned to this ticket.")

    def test_ticket_claim_unclaimed(self):
        self.ticket.assigned_to.clear()
        self.assertEqual(self.ticket.assigned_to.count(), 0)

        self.client.login(username=self.staff.username, password="Password123")
        claim_url = self.ticket.get_claim_url()
        response = self.client.post(claim_url, follow=True)

        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.assigned_to.filter(id=self.staff.id).exists())
        self.assertContains(response, "You have claimed this ticket.")

    def test_claim_already_claimed_ticket(self):
        self.ticket.assigned_to.add(self.staff)
        self.assertTrue(self.ticket.assigned_to.filter(id=self.staff.id).exists())

        self.client.login(username=self.staff.username, password="Password123")
        claim_url = self.ticket.get_claim_url()
        response = self.client.post(claim_url, follow=True)
        self.assertTrue(self.ticket.assigned_to.filter(id=self.staff.id).exists())
        self.assertContains(response, "You have already claimed this ticket.")
