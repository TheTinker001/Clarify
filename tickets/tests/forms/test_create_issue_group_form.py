from django.test import TestCase
from tickets.models import IssueGroup
from tickets.forms import IssueGroupForm


class IssueGroupFormTest(TestCase):
    """Tests for the IssueGroupForm form."""

    def setUp(self):
        self.issue_group = IssueGroup.objects.create(name="Test issue group")

    def test_form_has_correct_fields(self):
        form = IssueGroupForm()
        self.assertIn("name", form.fields)

    def test_valid_form(self):
        form = IssueGroupForm(data={"name": self.issue_group})
        self.assertTrue(form.is_valid())

    def test_blank_form_is_invalid(self):
        form = IssueGroupForm(data={"name": None})
        self.assertFalse(form.is_valid())
