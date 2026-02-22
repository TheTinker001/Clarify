"""Tests for the profile view."""

from django.contrib import messages
from django.test import TestCase
from django.urls import reverse
from tickets.forms import UserForm
from tickets.models import User
from tickets.models.ticket import Ticket
from tickets.tests.helpers import reverse_with_next


class ProfileViewTest(TestCase):
    """Test suite for the profile view."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.url = reverse("profile")
        self.form_input = {
            "first_name": "John2",
            "last_name": "Doe2",
            "username": "@johndoe2",
            "email": "johndoe2@example.org",
        }

    def test_profile_url(self):
        self.assertEqual(self.url, "/profile/")

    def test_get_profile(self):
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile.html")
        form = response.context["form"]
        self.assertTrue(isinstance(form, UserForm))
        self.assertEqual(form.instance, self.user)

    def test_get_profile_redirects_when_not_logged_in(self):
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )

    def test_unsuccesful_profile_update(self):
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["username"] = "BAD_USERNAME"
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = User.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile.html")
        form = response.context["form"]
        self.assertTrue(isinstance(form, UserForm))
        self.assertTrue(form.is_bound)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "@johndoe")
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Doe")
        self.assertEqual(self.user.email, "johndoe@example.org")

    def test_unsuccessful_profile_update_due_to_duplicate_username(self):
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["username"] = "@janedoe"
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = User.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile.html")
        form = response.context["form"]
        self.assertTrue(isinstance(form, UserForm))
        self.assertTrue(form.is_bound)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "@johndoe")
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Doe")
        self.assertEqual(self.user.email, "johndoe@example.org")

    def test_succesful_profile_update(self):
        self.client.login(username=self.user.username, password="Password123")
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_count = User.objects.count()
        self.assertEqual(after_count, before_count)
        response_url = reverse("dashboard")
        self.assertRedirects(
            response, response_url, status_code=302, target_status_code=200
        )
        self.assertTemplateUsed(response, "dashboard.html")
        messages_list = list(response.context["messages"])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].level, messages.SUCCESS)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "@johndoe2")
        self.assertEqual(self.user.first_name, "John2")
        self.assertEqual(self.user.last_name, "Doe2")
        self.assertEqual(self.user.email, "johndoe2@example.org")

    def test_post_profile_redirects_when_not_logged_in(self):
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.post(self.url, self.form_input)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )

    def test_profile_view_context_labels(self):
        self.user.faculties = "folsm,sspp"
        self.user.study_levels = "undergraduate"
        self.user.categories = "assessment,health_and_wellbeing"
        self.user.save()
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context

        self.assertEqual(context["faculty_list"], ["folsm", "sspp"])
        self.assertEqual(context["study_level_list"], ["undergraduate"])
        self.assertEqual(
            context["category_list"], ["assessment", "health_and_wellbeing"]
        )

        self.assertEqual(len(context["faculty_labels"]), 2)
        self.assertEqual(len(context["study_level_labels"]), 1)
        self.assertEqual(len(context["category_labels"]), 2)

        self.assertIn("Faculty", context)
        self.assertIn("StudyLevel", context)
        self.assertIn("Category", context)

    def test_get_profile_edit(self):
        url = reverse("profile_edit")
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile_edit.html")
        form = response.context["form"]
        self.assertTrue(isinstance(form, UserForm))
        self.assertEqual(form.instance, self.user)

    def test_post_profile_edit_success(self):
        url = reverse("profile_edit")
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["self_intro"] = "Edit intro"
        response = self.client.post(url, self.form_input, follow=True)
        self.user.refresh_from_db()
        self.assertRedirects(
            response, reverse("dashboard"), status_code=302, target_status_code=200
        )
        self.assertEqual(self.user.first_name, "John2")
        self.assertEqual(self.user.last_name, "Doe2")
        self.assertEqual(self.user.self_intro, "Edit intro")
        messages_list = list(response.context["messages"])
        self.assertTrue(any(m.level == messages.SUCCESS for m in messages_list))


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
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile_staff_edit.html")
        # Student should see no fields
        self.assertFalse(response.context["form"].fields)

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
        self.assertEqual(self.student.faculties, "")
        self.assertEqual(self.student.study_levels, "")
        self.assertEqual(self.student.categories, "")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile_staff_edit.html")
        self.assertFalse(response.context["form"].fields)

    def test_all_options_selected_by_default_for_new_staff(self):
        """When a staff user has no preferences saved, all options should be selected."""
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        form = response.context["form"]
        all_faculties = [code for code, _ in Ticket.Faculty.choices if code]
        all_study_levels = [code for code, _ in Ticket.StudyLevel.choices if code]
        all_categories = [code for code, _ in Ticket.Category.choices if code]
        self.assertEqual(form.fields["faculties"].initial, all_faculties)
        self.assertEqual(form.fields["study_levels"].initial, all_study_levels)
        self.assertEqual(form.fields["categories"].initial, all_categories)

    def test_saved_preferences_shown_instead_of_defaults(self):
        """When a staff user has saved preferences, those should be shown."""
        self.staff.faculties = "kbs,nmes"
        self.staff.study_levels = "undergraduate"
        self.staff.categories = "welfare"
        self.staff.save()
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        form = response.context["form"]
        self.assertEqual(form.fields["faculties"].initial, ["kbs", "nmes"])
        self.assertEqual(form.fields["study_levels"].initial, ["undergraduate"])
        self.assertEqual(form.fields["categories"].initial, ["welfare"])

    def test_redirects_when_not_logged_in(self):
        response = self.client.get(self.url)
        login_url = reverse_with_next("log_in", self.url)
        self.assertRedirects(
            response, login_url, status_code=302, target_status_code=200
        )
