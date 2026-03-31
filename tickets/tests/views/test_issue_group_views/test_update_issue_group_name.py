from django.test import TestCase
from django.urls import reverse
from tickets.tests.support import reverse_with_next
from tickets.models import IssueGroup, User


class UpdateIssueGroupViewTests(TestCase):
    """Tests for UpdateIssueGroupView"""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.get(username="@janedoe")
        self.issue_group = IssueGroup.objects.create(name="Test Issue Group")
        self.url = reverse(
            "edit_issue_group",
            kwargs={"slug": self.issue_group.slug},
        )

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse_with_next("log_in", self.url),
            fetch_redirect_response=False,
        )

    def test_staff_can_access_edit_page(self):
        self.client.login(username=self.staff.username, password="Password123")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "issue_group_edit.html")
        self.assertContains(response, "Test Issue Group")

    def test_non_staff_redirected_from_edit_page(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_post_valid_data(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(
            reverse(
                "edit_issue_group",
                kwargs={"slug": self.issue_group.slug},
            ),
            data={"name": "Updated Issue Group"},
        )
        self.issue_group.refresh_from_db()
        self.assertEqual(self.issue_group.name, "Updated Issue Group")
        self.assertEqual(response.status_code, 302)

    def test_invalid_post(self):
        self.client.login(username=self.staff.username, password="Password123")

        response = self.client.post(self.url, {"name": ""})

        self.issue_group.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.issue_group.name, "Test Issue Group")
