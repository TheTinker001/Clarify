"""Tests for the profile other user view."""

from django.test import TestCase
from django.urls import reverse
from tickets.models import User


class ProfileOtherUserViewTest(TestCase):
    """Test suite for the profile view of other users."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.staff_user = User.objects.get(username="@janedoe")
        self.student_user = User.objects.get(username="@johndoe")
        self.student_user.user_type = User.USER_TYPE_STUDENT
        self.student_user.preferred_name = "Johnny"
        self.student_user.pronouns = "he/him"
        self.student_user.student_id = "12345678"
        self.student_user.phone_number = "07700900000"
        self.student_user.faculty = "nmes"
        self.student_user.study_level = "undergraduate"
        self.student_user.graduation_year = 2026
        self.student_user.save()

        self.url_student = reverse("profile_other_user", kwargs={"username": self.student_user.username})
        self.url_staff = reverse("profile_other_user", kwargs={"username": self.staff_user.username})

    # --- Access control ---

    def test_unauthenticated_user_redirected(self):
        response = self.client.get(self.url_staff)
        self.assertEqual(response.status_code, 302)

    def test_staff_can_view_student_profile(self):
        self.client.login(username=self.staff_user.username, password="Password123")
        response = self.client.get(self.url_student)
        self.assertEqual(response.status_code, 200)

    def test_staff_can_view_staff_profile(self):
        self.client.login(username=self.staff_user.username, password="Password123")
        response = self.client.get(self.url_staff)
        self.assertEqual(response.status_code, 200)

    def test_student_can_view_staff_profile(self):
        self.client.login(username=self.student_user.username, password="Password123")
        response = self.client.get(self.url_staff)
        self.assertEqual(response.status_code, 200)

    def test_student_can_view_own_profile(self):
        self.client.login(username=self.student_user.username, password="Password123")
        response = self.client.get(self.url_student)
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_view_student_profile(self):
        other_student = User.objects.get(username="@petrapickles")
        other_student.user_type = User.USER_TYPE_STUDENT
        other_student.save()
        url = reverse("profile_other_user", kwargs={"username": other_student.username})
        self.client.login(username=self.student_user.username, password="Password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    # --- Email visibility ---

    def test_staff_sees_student_email(self):
        self.client.login(username=self.staff_user.username, password="Password123")
        response = self.client.get(self.url_student)
        self.assertContains(response, self.student_user.email)

    def test_student_cannot_see_staff_email(self):
        self.client.login(username=self.student_user.username, password="Password123")
        response = self.client.get(self.url_staff)
        self.assertNotContains(response, self.staff_user.email)

    # --- Student fields visible to staff ---

    def test_staff_sees_student_preferred_name(self):
        self.client.login(username=self.staff_user.username, password="Password123")
        response = self.client.get(self.url_student)
        self.assertContains(response, "Johnny")

    def test_staff_sees_student_pronouns(self):
        self.client.login(username=self.staff_user.username, password="Password123")
        response = self.client.get(self.url_student)
        self.assertContains(response, "he/him")

    def test_staff_sees_student_id(self):
        self.client.login(username=self.staff_user.username, password="Password123")
        response = self.client.get(self.url_student)
        self.assertContains(response, "12345678")

    def test_staff_sees_student_phone(self):
        self.client.login(username=self.staff_user.username, password="Password123")
        response = self.client.get(self.url_student)
        self.assertContains(response, "07700900000")

    def test_staff_sees_student_faculty(self):
        self.client.login(username=self.staff_user.username, password="Password123")
        response = self.client.get(self.url_student)
        self.assertContains(response, "Natural, Mathematical")

    def test_staff_sees_student_study_level(self):
        self.client.login(username=self.staff_user.username, password="Password123")
        response = self.client.get(self.url_student)
        self.assertContains(response, "Undergraduate")

    def test_staff_sees_student_graduation_year(self):
        self.client.login(username=self.staff_user.username, password="Password123")
        response = self.client.get(self.url_student)
        self.assertContains(response, "2026")

    # --- Template and context ---

    def test_correct_template_used(self):
        self.client.login(username=self.staff_user.username, password="Password123")
        response = self.client.get(self.url_student)
        self.assertTemplateUsed(response, "profile_other_user.html")

    def test_context_contains_profile_user(self):
        self.client.login(username=self.staff_user.username, password="Password123")
        response = self.client.get(self.url_student)
        self.assertEqual(response.context["profile_user"], self.student_user)

    def test_hide_email_true_for_student_viewer(self):
        self.client.login(username=self.student_user.username, password="Password123")
        response = self.client.get(self.url_staff)
        self.assertTrue(response.context["hide_email"])

    def test_hide_email_false_for_staff_viewer(self):
        self.client.login(username=self.staff_user.username, password="Password123")
        response = self.client.get(self.url_student)
        self.assertFalse(response.context["hide_email"])
