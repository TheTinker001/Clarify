from django.test import TestCase
from tickets.models import Ticket
from tickets.forms import TicketPriorityForm


class TicketFormTest(TestCase):
    """Tests for the ticket form."""

    def test_form_has_correct_fields(self):
        form = TicketPriorityForm()
        self.assertIn("priority", form.fields)

    def test_form_valid_with_priority_high(self):
        form = TicketPriorityForm(data={"priority": Ticket.Priority.HIGH})
        self.assertTrue(form.is_valid())

    def test_form_valid_with_priority_medium(self):
        form = TicketPriorityForm(data={"priority": Ticket.Priority.MEDIUM})
        self.assertTrue(form.is_valid())

    def test_form_valid_with_priority_low(self):
        form = TicketPriorityForm(data={"priority": Ticket.Priority.LOW})
        self.assertTrue(form.is_valid())

    def test_form_valid_with_priority_pending(self):
        form = TicketPriorityForm(data={"priority": Ticket.Priority.PENDING_PRIORITY})
        self.assertTrue(form.is_valid())

    def test_form_invalid_with_invalid_priority(self):
        form = TicketPriorityForm(data={"priority": "invalid_priority"})
        self.assertFalse(form.is_valid())
