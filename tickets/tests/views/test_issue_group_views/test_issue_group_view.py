"""Tests of the issue group view."""

from django.test import TestCase
from django.urls import reverse
from tickets.models import User, IssueGroup


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

    def test_issue_groups_are_in_context(self):
        self.client.login(username=self.staff.username, password="Password123")
        group1 = IssueGroup.objects.create(name="Test Issue Group 1")
        group2 = IssueGroup.objects.create(name="Test Issue Group 2")

        response = self.client.get(self.url)

        self.assertIn("issue_groups", response.context)
        self.assertIn("page_obj", response.context)
        self.assertIn("paginator", response.context)
        self.assertEqual(
            list(response.context["issue_groups"].object_list),
            [group1, group2],
        )

    def test_issue_groups_are_ordered_by_name(self):
        self.client.login(username=self.staff.username, password="Password123")
        IssueGroup.objects.create(name="a")
        IssueGroup.objects.create(name="b")
        IssueGroup.objects.create(name="c")

        response = self.client.get(self.url)

        names = [issue.name for issue in response.context["issue_groups"].object_list]
        self.assertEqual(names, ["a", "b", "c"])
