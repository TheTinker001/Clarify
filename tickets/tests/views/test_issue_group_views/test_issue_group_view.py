"""Tests of the issue group view."""

from django.test import TestCase
from django.urls import reverse
from tickets.helpers.pagination import get_page_slots
from tickets.tests.support import reverse_with_next
from tickets.models import User, IssueGroup
from clarify.settings import ITEMS_PER_PAGE


class IssueGroupViewTestCase(TestCase):
    """Tests for IssueGroupView."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.url = reverse("issue_group")
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.get(username="@janedoe")

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse_with_next("log_in", self.url),
            fetch_redirect_response=False,
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
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

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

    def test_issue_group_search_bar(self):
        self.client.login(username=self.staff.username, password="Password123")
        i1 = IssueGroup.objects.create(name="a")
        i2 = IssueGroup.objects.create(name="a2")
        IssueGroup.objects.create(name="b")
        IssueGroup.objects.create(name="c")

        response = self.client.get(self.url, {"searchTermForIG": "a"})
        self.assertEqual(response.status_code, 200)
        names = [issue for issue in response.context["issue_groups"]]
        self.assertEqual(names, [i1, i2])

    def test_issue_group_pagination_context_matches_dashboard_style(self):
        self.client.login(username=self.staff.username, password="Password123")

        for i in range(ITEMS_PER_PAGE + 5):
            IssueGroup.objects.create(name=f"Issue Group {i:02d}")

        response = self.client.get(self.url, {"page": 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["cur"], 2)
        self.assertEqual(
            response.context["max_pages"], response.context["paginator"].num_pages
        )
        self.assertEqual(
            response.context["page_slots"],
            get_page_slots(2, response.context["paginator"].num_pages),
        )
        self.assertEqual(response.context["querystring"], "")

    def test_issue_group_pagination_preserves_search_querystring(self):
        self.client.login(username=self.staff.username, password="Password123")

        for i in range(ITEMS_PER_PAGE + 5):
            IssueGroup.objects.create(name=f"Alpha Issue Group {i:02d}")

        response = self.client.get(
            self.url,
            {"searchTermForIG": "Alpha", "page": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["searchTermForIG"], "Alpha")
        self.assertEqual(response.context["querystring"], "searchTermForIG=Alpha")
