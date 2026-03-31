"""Unit tests of the staff preferences form."""

from django.test import TestCase
from tickets.models import User, Ticket
from tickets.forms import StaffPreferenceForm


class StaffPreferenceFormTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="@staff",
            first_name="Staff",
            last_name="User",
            email="staff@example.com",
            user_type=User.USER_TYPE_STAFF,
        )
        self.form_data = {
            "faculties": [Ticket.Faculty.FOLSM, Ticket.Faculty.SSPP],
            "study_levels": [Ticket.StudyLevel.UNDERGRADUATE],
            "categories": [
                Ticket.Category.ASSESSMENT,
                Ticket.Category.HEALTH_AND_WELLBEING,
            ],
        }

    def get_form(self, instance=None, data=None):
        if data is None:
            data = self.form_data
        if instance is None:
            instance = self.user
        return StaffPreferenceForm(data=data, instance=instance)

    def test_valid_for_staff(self):
        form = self.get_form()
        self.assertTrue(form.is_valid())

    def test_saves_preferences(self):
        form = self.get_form()
        form.is_valid()
        user = form.save()
        self.assertEqual(
            user.faculties, f"{Ticket.Faculty.FOLSM},{Ticket.Faculty.SSPP}"
        )
        self.assertEqual(user.study_levels, Ticket.StudyLevel.UNDERGRADUATE)
        self.assertEqual(
            user.categories,
            f"{Ticket.Category.ASSESSMENT},{Ticket.Category.HEALTH_AND_WELLBEING}",
        )

    def test_only_staff_can_edit(self):
        form = self.get_form()
        self.assertTrue(form.is_valid())
        student = User.objects.create(
            username="@student",
            first_name="Student",
            last_name="User",
            email="student@example.com",
            user_type=User.USER_TYPE_STUDENT,
        )
        form = self.get_form(instance=student)
        self.assertFalse(form.is_valid())
        self.assertIn("Only staff can edit preferences.", str(form.errors))
