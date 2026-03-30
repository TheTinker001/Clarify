from django.test import TestCase
from tickets.models import User, Ticket
from tickets.forms import TicketFieldsForm


class TicketFieldsFormTest(TestCase):
    """Tests for the ticket fields form."""

    def setUp(self):
        self.student = User.objects.create_user(
            username="@student",
            password="Password123",
            user_type=User.USER_TYPE_STUDENT,
        )
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty=Ticket.Faculty.NMES,
            study_level=Ticket.StudyLevel.UNDERGRADUATE,
            category=Ticket.Category.OTHER,
            subject="Test subject",
            body="Test body",
        )

    def test_form_has_correct_fields(self):
        form = TicketFieldsForm(instance=self.ticket)
        self.assertIn("faculty", form.fields)
        self.assertIn("study_level", form.fields)
        self.assertIn("category", form.fields)

    def test_form_valid_with_faculty(self):
        form = TicketFieldsForm(
            data={
                "faculty": Ticket.Faculty.KBS,
                "study_level": Ticket.StudyLevel.POSTGRADUATE_RESEARCH,
                "category": Ticket.Category.WELFARE,
            },
            instance=self.ticket,
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid_with_invalid_fields(self):
        form = TicketFieldsForm(
            data={
                "faculty": "invalid_faculty",
                "study_level": "invalid_study_level",
                "category": "invalid_category",
            },
            instance=self.ticket,
        )
        self.assertFalse(form.is_valid())
