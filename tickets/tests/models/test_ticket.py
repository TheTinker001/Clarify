"""Tests for the Ticket model."""
from django.test import TestCase
from tickets.models import Ticket, User


class TicketModelTestCase(TestCase):
    """Test suite for the Ticket model."""

    fixtures = ['tickets/tests/fixtures/default_user.json']

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')

    def test_ticket_string(self):
        ticket = Ticket.objects.create(
            title='Reset my password',
            description='Please reset my password.',
            story_points=3,
            created_by=self.user,
        )
        self.assertEqual(str(ticket), f"#{ticket.pk} Reset my password")

    def test_ticket_defaults(self):
        ticket = Ticket.objects.create(
            title='Update email address',
            created_by=self.user,
        )
        self.assertEqual(ticket.status, Ticket.Status.OPEN)
        self.assertEqual(ticket.story_points, 1)
