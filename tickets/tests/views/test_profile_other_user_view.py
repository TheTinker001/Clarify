"""Tests for the profile other user view."""

from django.http import Http404
from django.test import TestCase
from django.urls import reverse
from tickets.models import User
from tickets.views.profile_other_user_view import ProfileOtherUserView


class ProfileOtherUserViewTest(TestCase):
    """Test suite for the profile view of other users."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.get(username="@janedoe")
        self.other_student = User.objects.get(username="@petrapickles")

    def test_staff_can_view_any_user_profile(self):
        self.client.login(username=self.staff.username, password="Password123")
        url = reverse(
            "profile_other_user", kwargs={"username": self.other_student.username}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile_other_user.html")
        self.assertEqual(response.context["profile_user"], self.other_student)
        self.assertTrue(response.context["can_view_email"])
        self.assertTrue(response.context["can_view_student_details"])
        self.assertContains(response, self.other_student.preferred_name)
        self.assertContains(response, self.other_student.pronouns)
        self.assertContains(response, self.other_student.student_id)
        self.assertContains(response, self.other_student.email)
        self.assertContains(response, "Social Science")
        self.assertContains(response, self.other_student.study_level_label)

    def test_student_can_view_staff_profile_without_staff_email(self):
        self.client.login(username=self.student.username, password="Password123")
        url = reverse("profile_other_user", kwargs={"username": self.staff.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile_other_user.html")
        self.assertEqual(response.context["profile_user"], self.staff)
        self.assertFalse(response.context["can_view_email"])
        self.assertFalse(response.context["can_view_student_details"])
        self.assertContains(response, self.staff.preferred_name)
        self.assertContains(response, self.staff.pronouns)
        self.assertNotContains(response, self.staff.email)
        self.assertNotContains(response, "Student ID:")

    def test_student_cannot_view_other_student_profile(self):
        self.client.login(username=self.student.username, password="Password123")
        url = reverse(
            "profile_other_user", kwargs={"username": self.other_student.username}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_user_can_view_own_profile_route(self):
        self.client.login(username=self.student.username, password="Password123")
        url = reverse("profile_other_user", kwargs={"username": self.student.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["can_view_email"])
        self.assertTrue(response.context["can_view_student_details"])
        self.assertContains(response, self.student.student_id)
