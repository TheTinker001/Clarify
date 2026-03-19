from django.test import TestCase
from django.urls import reverse
from tickets.models import User, IssueGroup, Ticket


class IssueGroupDetailViewTestCase(TestCase):
    """Tests for IssueGroupDetailView."""

    fixtures = ["tickets/tests/fixtures/default_user.json"]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.create_user(
            username="@staffuser",
            password="Password123",
            user_type=User.USER_TYPE_STAFF,
        )
        self.issue_group = IssueGroup.objects.create(name="Test Issue Group")
        self.url = reverse(
            "issue_group_detail",
            kwargs={"slug": self.issue_group.slug},
        )

    def test_staff_can_access_issue_group_detail(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "issue_group_detail.html")

    def test_non_staff_redirected_from_detail_page(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("dashboard"))

    def test_returns_404_for_nonexistent_issue_group(self):
        self.client.login(username=self.staff.username, password="Password123")
        bad_url = reverse("issue_group_detail", kwargs={"slug": "does-not-exist"})
        response = self.client.get(bad_url)
        self.assertEqual(response.status_code, 404)

    def test_all_issue_group_tickets_viewable(self):
        issue_group2 = IssueGroup.objects.create(name="Test Issue Group 2")
        t1 = Ticket.objects.create(
            student=self.student,
            assigned_to=self.staff,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test",
            body="Test",
            issue_group=self.issue_group,
        )
        t2 = Ticket.objects.create(
            student=self.student,
            assigned_to=self.staff,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test2",
            body="Test2",
            issue_group=self.issue_group,
        )
        t3 = Ticket.objects.create(
            student=self.student,
            assigned_to=self.staff,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test2",
            body="Test2",
            issue_group=issue_group2,
        )
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        displayed_tickets = list(response.context["tickets"].object_list)
        self.assertIn(t1, displayed_tickets)
        self.assertIn(t2, displayed_tickets)
        self.assertNotIn(t3, displayed_tickets)
        self.assertEqual(len(displayed_tickets), 2)
