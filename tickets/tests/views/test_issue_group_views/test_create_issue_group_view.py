from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from tickets.tests.support import reverse_with_next
from tickets.models import User, IssueGroup


class IssueGroupCreateViewTestCase(TestCase):
    """Tests for IssueGroupCreateView."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.get(username="@janedoe")
        self.url = reverse("create_issue_group")

    def test_url(self):
        self.assertEqual(self.url, "/issues/create/")

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse_with_next("log_in", self.url),
            fetch_redirect_response=False,
        )

    def test_staff_can_access_create_issue_group_page(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "create_issue_group.html")

    def test_non_staff_redirected_from_create_page(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_create_valid_issue_group(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        response = self.client.post(
            self.url,
            {"name": "Test Issue Group"},
        )
        self.assertEqual(IssueGroup.objects.count(), 1)
        issue_group = IssueGroup.objects.get()
        self.assertEqual(issue_group.name, "Test Issue Group")
        self.assertRedirects(response, reverse("issue_group"))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(m.message == "Issue group created successfully!" for m in messages)
        )

    def test_create_invalid_issue_group(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        response = self.client.post(
            self.url,
            {"name": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(IssueGroup.objects.count(), 0)
