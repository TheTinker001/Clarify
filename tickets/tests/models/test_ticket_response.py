"""Unit tests for the TicketResponse model."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from tickets.models import Ticket
from tickets.models.ticket_response import TicketResponse

User = get_user_model()


class TicketResponseModelTestCase(TestCase):
    """Tests for the TicketResponse model."""

    def setUp(self):
        self.student = User.objects.create_user(
            username="@student",
            email="student@test.com",
            password="Password123",
            first_name="Test",
            last_name="Student",
            user_type="student",
        )
        self.staff = User.objects.create_user(
            username="@staff",
            email="staff@test.com",
            password="Password123",
            first_name="Staff",
            last_name="User",
            user_type="staff",
        )
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Test ticket",
            body="Test body.",
        )

    def test_create_response(self):
        response = TicketResponse.objects.create(
            ticket=self.ticket, author=self.staff, body="A response."
        )
        self.assertEqual(response.ticket, self.ticket)
        self.assertEqual(response.author, self.staff)
        self.assertEqual(response.body, "A response.")
        self.assertIsNotNone(response.created_at)

    def test_str_representation(self):
        response = TicketResponse.objects.create(
            ticket=self.ticket, author=self.staff, body="A response."
        )
        self.assertIn("@staff", str(response))
        self.assertIn(str(self.ticket.pk), str(response))

    def test_responses_ordered_by_created_at(self):
        r1 = TicketResponse.objects.create(
            ticket=self.ticket, author=self.staff, body="First."
        )
        r2 = TicketResponse.objects.create(
            ticket=self.ticket, author=self.student, body="Second."
        )
        responses = list(self.ticket.responses.all())
        self.assertEqual(responses[0], r1)
        self.assertEqual(responses[1], r2)

    def test_response_deleted_when_ticket_deleted(self):
        TicketResponse.objects.create(
            ticket=self.ticket, author=self.staff, body="Will be deleted."
        )
        self.assertEqual(TicketResponse.objects.count(), 1)
        self.ticket.delete()
        self.assertEqual(TicketResponse.objects.count(), 0)

    def test_response_deleted_when_author_deleted(self):
        TicketResponse.objects.create(
            ticket=self.ticket, author=self.staff, body="Will be deleted."
        )
        self.assertEqual(TicketResponse.objects.count(), 1)
        self.staff.delete()
        self.assertEqual(TicketResponse.objects.count(), 0)
