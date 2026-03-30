"""Tests for the profile view."""

from django.test import TestCase
from django.contrib import messages
from django.urls import reverse
from tickets.tests.helpers import _reverse_with_next
from tickets.models import User
from tickets.forms import UserForm


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
        redirect_url = _reverse_with_next("log_in", self.url)
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
        redirect_url = _reverse_with_next("log_in", self.url)
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

    def test_get_labels_various_cases(self):
        from tickets.models.ticket import Ticket
        from tickets.views.profile_view import UserProfileContext

        ctx = UserProfileContext()
        # Valid code
        self.user.faculties = Ticket.Faculty.choices[1][0]
        self.user.save()
        self.assertEqual(
            ctx.get_profile_context(self.user)["faculty_labels"],
            [Ticket.Faculty(self.user.faculties).label] if self.user.faculties else [],
        )
        # Empty codes
        self.user.faculties = ""
        self.user.save()
        self.assertEqual(ctx.get_profile_context(self.user)["faculty_labels"], [])
        # Invalid code
        self.user.faculties = "notarealcode"
        self.user.save()
        self.assertEqual(ctx.get_profile_context(self.user)["faculty_labels"], [])

    def test_profile_edit_does_not_update_locked_student_fields(self):
        self.client.login(username=self.user.username, password="Password123")

        original_student_id = self.user.student_id
        original_faculty = self.user.faculty

        response = self.client.post(
            reverse("profile_edit"),
            {
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "username": self.user.username,
                "email": self.user.email,
                "preferred_name": "New Pref",
                "pronouns": "they/them",
                "phone_number": "07123456789",
                "student_id": "99999999",
                "faculty": "kbs",
            },
            follow=True,
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.preferred_name, "New Pref")
        self.assertEqual(self.user.pronouns, "they/them")
        self.assertEqual(self.user.phone_number, "07123456789")
        self.assertEqual(self.user.student_id, original_student_id)
        self.assertEqual(self.user.faculty, original_faculty)
