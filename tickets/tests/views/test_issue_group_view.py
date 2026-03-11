"""Tests of the issue group view."""

from django.test import TestCase
from django.urls import reverse
from tickets.models import User


class IssueGroupViewTestCase(TestCase):
    """Tests of the issue group view."""

    fixtures = ["tickets/tests/fixtures/default_user.json"]

    def setUp(self):
        self.url = reverse("issue_group")
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.create_user(
            username="@staffuser",
            password="Password123",
            user_type=User.USER_TYPE_STAFF,
        )

    def test_issue_group_url(self):
        self.assertEqual(self.url, "/issues/")

    def test_template_used(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "issue_group.html")

    def test_redirect_for_non_staff(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url, follow=True)
        redirect_url = reverse("dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
