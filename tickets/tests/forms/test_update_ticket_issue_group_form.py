from django.test import TestCase
from tickets.models import IssueGroup
from tickets.forms import TicketIssueGroupForm


class TicketIssueGroupFormTest(TestCase):
    """Tests for the TicketIssueGroupForm form."""

    def setUp(self):
        self.issue_group = IssueGroup.objects.create(name="Test issue group")

    def test_form_has_correct_fields(self):
        form = TicketIssueGroupForm()
        self.assertIn("issue_group", form.fields)

    def test_valid_form(self):
        form = TicketIssueGroupForm(data={"issue_group": self.issue_group})
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        form = TicketIssueGroupForm(data={"issue_group": "dasfadsfa"})
        self.assertFalse(form.is_valid())

    def test_blank_form_is_valid(self):
        form = TicketIssueGroupForm(data={"issue_group": None})
        self.assertTrue(form.is_valid())
