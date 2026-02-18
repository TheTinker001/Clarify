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
        self.user = User.objects.get(username="@johndoe")
        self.user.user_type = User.USER_TYPE_STAFF
        self.other_user = User.objects.get(username="@janedoe")
        self.user.save()
        self.url = reverse(
            "profile_other_user", kwargs={"username": self.other_user.username}
        )

    def test_get_other_user_profile(self):
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile_other_user.html")
        profile_user = response.context["profile_user"]
        self.assertEqual(profile_user, self.other_user)
