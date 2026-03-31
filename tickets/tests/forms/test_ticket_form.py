from django.test import TestCase
from django_summernote.widgets import SummernoteWidget
from django.core.files.uploadedfile import SimpleUploadedFile
from tickets.models import Ticket
from tickets.forms import TicketForm
from clarify.settings import BODY_LENGTH_MAX


class TicketFormTest(TestCase):
    """Tests for the ticket form."""

    def test_form_has_correct_fields(self):
        form = TicketForm()
        self.assertEqual(
            list(form.fields.keys()),
            [
                "faculty",
                "study_level",
                "category",
                "priority",
                "subject",
                "body",
                "attachments",
            ],
        )

    def test_form_valid_data(self):
        form_data = {
            "faculty": "kbs",
            "study_level": "undergraduate",
            "category": "health_and_wellbeing",
            "priority": "high",
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
        self.assertIn("priority", form.errors)
        self.assertIn("subject", form.errors)
        self.assertIn("body", form.errors)

    def test_form_missing_subject(self):
        form_data = {
            "faculty": "kbs",
            "study_level": "undergraduate",
            "category": "health_and_wellbeing",
            "priority": "high",
            "body": "Test body",
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("subject", form.errors)

    def test_form_missing_priority(self):
        form_data = {
            "faculty": "kbs",
            "study_level": "undergraduate",
            "category": "health_and_wellbeing",
            "subject": "Test subject",
            "body": "Test body",
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("priority", form.errors)

    def test_form_missing_body(self):
        form_data = {
            "faculty": "kbs",
            "study_level": "undergraduate",
            "category": "health_and_wellbeing",
            "priority": "high",
            "subject": "Test subject",
        }
        form = TicketForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("body", form.errors)

    def test_body_widget_is_textarea(self):
        form = TicketForm()
        self.assertIsInstance(form.fields["body"].widget, SummernoteWidget)

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
                "category": "health_and_wellbeing",
                "priority": "high",
                "subject": "Test",
                "body": "Test body",
            }
            form = TicketForm(data=form_data)
            if faculty_code != "":
                self.assertTrue(
                    form.is_valid(), f"Faculty {faculty_code} should be valid"
                )
            else:
                self.assertFalse(
                    form.is_valid(), f"Faculty {faculty_code} should be valid"
                )

    def test_all_study_level_choices_valid(self):
        for level_code, _ in Ticket.StudyLevel.choices:
            form_data = {
                "faculty": "kbs",
                "study_level": level_code,
                "category": "health_and_wellbeing",
                "priority": "high",
                "subject": "Test",
                "body": "Test body",
            }
            form = TicketForm(data=form_data)
            if level_code != "":
                self.assertTrue(
                    form.is_valid(), f"Study level {level_code} should be valid"
                )
            else:
                self.assertFalse(
                    form.is_valid(), f"Study level {level_code} should be valid"
                )

    def test_all_category_choices_valid(self):
        for category_code, _ in Ticket.Category.choices:
            form_data = {
                "faculty": "kbs",
                "study_level": "undergraduate",
                "category": category_code,
                "priority": "high",
                "subject": "Test",
                "body": "Test body",
            }
            form = TicketForm(data=form_data)

            if category_code != "":
                self.assertTrue(
                    form.is_valid(), f"Category {category_code} should be valid"
                )
            else:
                self.assertFalse(
                    form.is_valid(), f"Category {category_code} should be valid"
                )

    def test_attachment_field_is_optional(self):
        form = TicketForm()
        self.assertFalse(form.fields["attachments"].required)

    def test_attachment_accepts_valid_file_types(self):
        """Test that attachment accepts allowed file extensions."""

        file = SimpleUploadedFile(
            "test.pdf", b"file content", content_type="application/pdf"
        )
        data = {
            "faculty": "kbs",
            "study_level": "undergraduate",
            "category": "assessment",
            "priority": "high",
            "subject": "Test subject",
            "body": "Test body",
        }
        form = TicketForm(data=data, files={"attachments": file})
        self.assertTrue(form.is_valid())

    def test_attachment_rejects_invalid_file_types(self):

        file = SimpleUploadedFile(
            "test.exe", b"file content", content_type="application/exe"
        )
        data = {
            "faculty": "kbs",
            "study_level": "undergraduate",
            "category": "assessment",
            "priority": "high",
            "subject": "Test subject",
            "body": "Test body",
        }
        form = TicketForm(data=data, files={"attachments": file})
        self.assertFalse(form.is_valid())
        self.assertIn("attachments", form.errors)

    def test_attachment_rejects_large_files(self):

        large_content = b"x" * (6 * 1024 * 1024)
        file = SimpleUploadedFile(
            "large_file.pdf", large_content, content_type="application/pdf"
        )

        data = {
            "faculty": "kbs",
            "study_level": "undergraduate",
            "category": "assessment",
            "priority": "high",
            "subject": "Test subject",
            "body": "Test body",
        }
        form = TicketForm(data=data, files={"attachments": file})
        self.assertFalse(form.is_valid())
        self.assertIn("attachments", form.errors)

    def test_attachment_accepts_valid_file_size(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        small_content = b"x" * (1 * 1024 * 1024)
        file = SimpleUploadedFile(
            "small_file.pdf", small_content, content_type="application/pdf"
        )

        data = {
            "faculty": "kbs",
            "study_level": "undergraduate",
            "category": "assessment",
            "priority": "high",
            "subject": "Test subject",
            "body": "Test body",
        }
        form = TicketForm(data=data, files={"attachment": file})
        self.assertTrue(form.is_valid())

    def test_body_too_long_is_invalid(self):
        form = TicketForm(
            data={
                "faculty": Ticket.Faculty.AH,
                "study_level": Ticket.StudyLevel.UNDERGRADUATE,
                "category": Ticket.Category.HEALTH_AND_WELLBEING,
                "subject": "Test subject",
                "body": "a" * (BODY_LENGTH_MAX + 1),
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("body", form.errors)
        self.assertNotIn("faculty", form.errors)
        self.assertNotIn("study_level", form.errors)
        self.assertNotIn("category", form.errors)
