"""Unit tests for the TicketResponseForm."""
from django.test import TestCase
from tickets.forms.ticket_response_form import TicketResponseForm


class TicketResponseFormTestCase(TestCase):
    """Tests for the TicketResponseForm."""

    def test_valid_form(self):
        form = TicketResponseForm(data={"body": "This is a valid response."})
        self.assertTrue(form.is_valid())

    def test_blank_body_is_invalid(self):
        form = TicketResponseForm(data={"body": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("body", form.errors)

    def test_form_has_body_field(self):
        form = TicketResponseForm()
        self.assertIn("body", form.fields)

    def test_body_widget_is_textarea(self):
        form = TicketResponseForm()
        from django import forms
        self.assertIsInstance(form.fields["body"].widget, forms.Textarea)

    def test_body_placeholder(self):
        form = TicketResponseForm()
        self.assertEqual(
            form.fields["body"].widget.attrs.get("placeholder"),
            "Write your response...",
        )
