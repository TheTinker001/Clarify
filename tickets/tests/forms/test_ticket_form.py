from django.test import TestCase
from tickets.models import Ticket
from tickets.forms import TicketForm


class TicketFormTest(TestCase):
    """Tests for the ticket form."""

    def test_form_has_correct_fields(self):
        form = TicketForm()
        self.assertEqual(
            list(form.fields.keys()),
            ["faculty", "study_level", "category", "subject", "body"],
        )

    def test_form_valid_data(self):
        form_data = {
            "faculty": "kbs",
            "study_level": "undergraduate",
            "category": "health",
            "subject": "Test Subject",
            "body": "Test body content",
        }
        form = TicketForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_missing_required_fields(self):
        form_data = {
            "faculty": "kbs",
            "study_level": "undergraduate",
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("category", form.errors)
        self.assertIn("subject", form.errors)
        self.assertIn("body", form.errors)

    def test_form_missing_subject(self):
        form_data = {
            "faculty": "kbs",
            "study_level": "undergraduate",
            "category": "health",
            "body": "Test body",
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("subject", form.errors)

    def test_form_missing_body(self):
        form_data = {
            "faculty": "kbs",
            "study_level": "undergraduate",
            "category": "health",
            "subject": "Test subject",
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("body", form.errors)

    def test_body_widget_is_textarea(self):
        form = TicketForm()
        self.assertEqual(form.fields["body"].widget.attrs["rows"], 10)

    def test_form_does_not_include_student_field(self):
        form = TicketForm()
        self.assertNotIn("student", form.fields)

    def test_form_does_not_include_status_field(self):
        form = TicketForm()
        self.assertNotIn("status", form.fields)

    def test_all_faculty_choices_valid(self):
        for faculty_code, _ in Ticket.Faculty.choices:
            form_data = {
                "faculty": faculty_code,
                "study_level": "undergraduate",
                "category": "health",
                "subject": "Test",
                "body": "Test body",
            }
            form = TicketForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Faculty {faculty_code} should be valid")

    def test_all_study_level_choices_valid(self):
        for level_code, _ in Ticket.StudyLevel.choices:
            form_data = {
                "faculty": "kbs",
                "study_level": level_code,
                "category": "health",
                "subject": "Test",
                "body": "Test body",
            }
            form = TicketForm(data=form_data)
            self.assertTrue(
                form.is_valid(), f"Study level {level_code} should be valid"
            )

    def test_all_category_choices_valid(self):
        for category_code, _ in Ticket.Category.choices:
            form_data = {
                "faculty": "kbs",
                "study_level": "undergraduate",
                "category": category_code,
                "subject": "Test",
                "body": "Test body",
            }
            form = TicketForm(data=form_data)
            self.assertTrue(
                form.is_valid(), f"Category {category_code} should be valid"
            )
