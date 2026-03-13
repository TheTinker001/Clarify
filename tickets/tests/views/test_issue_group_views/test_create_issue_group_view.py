from django.test import TestCase
from django.urls import reverse
from tickets.models import User, IssueGroup
from django.contrib.messages import get_messages


class IssueGroupCreateViewTestCase(TestCase):

    fixtures = ["tickets/tests/fixtures/default_user.json"]

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

    def test_staff_can_access_create_issue_group_page(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "create_issue_group.html")

    def test_non_staff_redirected_from_create_page(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("dashboard"))

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
