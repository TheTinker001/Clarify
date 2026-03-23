"""Tests of the sign up view."""

from django.contrib.auth.hashers import check_password
from django.test import TestCase
from django.urls import reverse
from tickets.forms import SignUpForm
from tickets.models import Ticket, User
from tickets.tests.helpers import LogInTester


class SignUpViewTestCase(TestCase, LogInTester):
    """Tests of the sign up view."""

    fixtures = ["tickets/tests/fixtures/default_user.json"]

    def setUp(self):
        self.url = reverse("sign_up")
        self.form_input = {
            "first_name": "Jimmy",
            "last_name": "Atom",
            "preferred_name": "Jim",
            "pronouns": "he/him",
            "username": "@jimmyatom",
            "email": "jimmyatom@example.org",
            "user_type": User.USER_TYPE_STUDENT,
            "student_id": "87654321",
            "phone_number": "+44 0000 008767",
            "faculty": Ticket.Faculty.FOLSM,
            "study_level": Ticket.StudyLevel.UNDERGRADUATE,
            "graduation_year": 2027,
            "new_password": "Password123",
            "password_confirmation": "Password123",
        }
        self.user = User.objects.get(username="@johndoe")

    def test_sign_up_url(self):
        self.assertEqual(self.url, "/sign_up/")

    def test_get_sign_up(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sign_up.html")
        form = response.context["form"]
        self.assertTrue(isinstance(form, SignUpForm))
        self.assertFalse(form.is_bound)

    def test_get_sign_up_redirects_when_logged_in(self):
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, follow=True)
        redirect_url = reverse("dashboard")
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertTemplateUsed(response, "dashboard.html")

    def test_unsuccesful_sign_up(self):
        self.form_input["username"] = "BAD_USERNAME"
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = User.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sign_up.html")
        form = response.context["form"]
        self.assertTrue(isinstance(form, SignUpForm))
        self.assertTrue(form.is_bound)
        self.assertFalse(self._is_logged_in())

    def test_unsuccessful_student_sign_up_without_required_student_fields(self):
        self.form_input["student_id"] = ""
        self.form_input["faculty"] = ""
        self.form_input["study_level"] = ""
        self.form_input["graduation_year"] = ""
        response = self.client.post(self.url, self.form_input)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("student_id", form.errors)
        self.assertIn("faculty", form.errors)
        self.assertIn("study_level", form.errors)
        self.assertIn("graduation_year", form.errors)

    def test_succesful_sign_up_as_student(self):
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_count = User.objects.count()
        self.assertEqual(after_count, before_count + 1)
        response_url = reverse("dashboard")
        self.assertRedirects(
            response, response_url, status_code=302, target_status_code=200
        )
        self.assertTemplateUsed(response, "dashboard.html")
        user = User.objects.get(username="@jimmyatom")
        self.assertEqual(user.first_name, "Jimmy")
        self.assertEqual(user.last_name, "Atom")
        self.assertEqual(user.preferred_name, "Jim")
        self.assertEqual(user.pronouns, "he/him")
        self.assertEqual(user.email, "jimmyatom@example.org")
        self.assertEqual(user.user_type, User.USER_TYPE_STUDENT)
        self.assertEqual(user.student_id, "87654321")
        self.assertEqual(user.phone_number, "+44 0000 008767")
        self.assertEqual(user.faculty, Ticket.Faculty.FOLSM)
        self.assertEqual(user.study_level, Ticket.StudyLevel.UNDERGRADUATE)
        self.assertEqual(user.graduation_year, 2027)
        is_password_correct = check_password("Password123", user.password)
        self.assertTrue(is_password_correct)
        self.assertTrue(self._is_logged_in())

    def test_succesful_sign_up_as_staff_redirects_to_staffedit(self):
        self.form_input["user_type"] = User.USER_TYPE_STAFF
        self.form_input["username"] = "@staffjimmy"
        self.form_input["email"] = "staffjimmy@example.org"
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_count = User.objects.count()
        self.assertEqual(after_count, before_count + 1)
        response_url = reverse("profile_staff_edit")
        self.assertRedirects(
            response, response_url, status_code=302, target_status_code=200
        )
        self.assertTemplateUsed(response, "profile_staff_edit.html")
        user = User.objects.get(username="@staffjimmy")
        self.assertEqual(user.user_type, User.USER_TYPE_STAFF)
        self.assertEqual(user.preferred_name, "Jim")
        self.assertEqual(user.pronouns, "he/him")
        self.assertEqual(user.student_id, "")
        self.assertEqual(user.phone_number, "")
        self.assertEqual(user.faculty, "")
        self.assertEqual(user.study_level, "")
        self.assertIsNone(user.graduation_year)
        self.assertTrue(self._is_logged_in())

    def test_post_sign_up_redirects_when_logged_in(self):
        self.client.login(username=self.user.username, password="Password123")
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_count = User.objects.count()
        self.assertEqual(after_count, before_count)
        redirect_url = reverse("dashboard")
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertTemplateUsed(response, "dashboard.html")
