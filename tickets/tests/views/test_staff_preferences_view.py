"""Tests for the staff preferences view."""

from django.test import TestCase
from django.urls import reverse
from tickets.models import User, Ticket


class StaffPreferencesViewTestCase(TestCase):
    """Test suite for the staff preferences view."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.staff = User.objects.create_user(
            username="@staff",
            first_name="Staff",
            last_name="User",
            email="staff@example.org",
            password="Password123",
            user_type=User.USER_TYPE_STAFF,
        )
        self.student = User.objects.get(username="@johndoe")
        self.url = reverse("profile_staff_edit")
        self.form_input = {
            "faculties": ["folsm", "sspp"],
            "study_levels": ["undergraduate"],
            "categories": ["assessment", "health_and_wellbeing"],
        }

    def test_get_staff_preferences_as_staff(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile_staff_edit.html")
        self.assertIn("form", response.context)
        self.assertTrue(response.context["form"].fields)

    def test_get_staff_preferences_as_student(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_post_staff_preferences_as_staff(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(self.url, self.form_input, follow=True)
        self.staff.refresh_from_db()
        self.assertRedirects(
            response, reverse("profile"), status_code=302, target_status_code=200
        )
        self.assertEqual(self.staff.faculties, "folsm,sspp")
        self.assertEqual(self.staff.study_levels, "undergraduate")
        self.assertEqual(self.staff.categories, "assessment,health_and_wellbeing")

    def test_post_staff_preferences_as_student(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(self.url, self.form_input)
        self.student.refresh_from_db()
        # Student should not be able to update preferences
        self.assertEqual(response.status_code, 404)

    def test_redirects_when_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_get_form_clears_fields_for_non_staff_user(self):
        from django.test import RequestFactory
        from tickets.views.staff_preferences_view import (
            StaffPreferencesView,
        )

        rf = RequestFactory()
        request = rf.get(self.url)
        request.user = self.student  # non-staff user from fixtures

        view = StaffPreferencesView()
        view.request = request
        view.object = self.student

        form = view.get_form()

        # fields should be cleared for non-staff users
        self.assertFalse(form.fields)

    def test_get_staff_preferences_restores_multiple_faculties_from_db(self):
        self.staff.faculties = "folsm,sspp"
        self.staff.save()

        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertEqual(form["faculties"].value(), ["folsm", "sspp"])

    def test_get_staff_preferences_restores_multiple_study_levels_from_db(self):
        self.staff.study_levels = (
            f"{Ticket.StudyLevel.UNDERGRADUATE},{Ticket.StudyLevel.OTHER}"
        )
        self.staff.save()

        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertEqual(
            form["study_levels"].value(),
            [Ticket.StudyLevel.UNDERGRADUATE, Ticket.StudyLevel.OTHER],
        )

    def test_get_staff_preferences_restores_multiple_categories_from_db(self):
        self.staff.categories = (
            f"{Ticket.Category.WELFARE},{Ticket.Category.UNI_PROCEDURES_REGULATIONS}"
        )
        self.staff.save()

        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertEqual(
            form["categories"].value(),
            [Ticket.Category.WELFARE, Ticket.Category.UNI_PROCEDURES_REGULATIONS],
        )

    def test_all_options_selected_by_default_for_new_staff(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        form = response.context["form"]
        all_faculties = [code for code, _ in Ticket.Faculty.choices if code]
        all_study_levels = [code for code, _ in Ticket.StudyLevel.choices if code]
        all_categories = [code for code, _ in Ticket.Category.choices if code]
        self.assertEqual(form.initial["faculties"], all_faculties)
        self.assertEqual(form.initial["study_levels"], all_study_levels)
        self.assertEqual(form.initial["categories"], all_categories)

    def test_saved_preferences_shown_instead_of_defaults(self):
        self.staff.faculties = "kbs,nmes"
        self.staff.study_levels = "undergraduate"
        self.staff.categories = "welfare"
        self.staff.save()
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        form = response.context["form"]
        self.assertEqual(form.initial["faculties"], ["kbs", "nmes"])
        self.assertEqual(form.initial["study_levels"], ["undergraduate"])
        self.assertEqual(form.initial["categories"], ["welfare"])

    def test_staff_preferences_form_excludes_select_placeholder_choice(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]

        self.assertNotIn("", [v for v, _ in form.fields["faculties"].choices])
        self.assertNotIn("", [v for v, _ in form.fields["study_levels"].choices])
        self.assertNotIn("", [v for v, _ in form.fields["categories"].choices])
