from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from tickets.tests.helpers import _reverse_with_next
from tickets.models import User, IssueGroup, Ticket, IssueUpdate


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

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            _reverse_with_next("log_in", self.url),
            fetch_redirect_response=False,
        )

    def test_staff_can_access_issue_group_detail(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "issue_group_detail.html")

    def test_non_staff_redirected_from_detail_page(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_returns_404_for_nonexistent_issue_group(self):
        self.client.login(username=self.staff.username, password="Password123")
        bad_url = reverse("issue_group_detail", kwargs={"slug": "does-not-exist"})
        response = self.client.get(bad_url)
        self.assertEqual(response.status_code, 404)

    def test_all_issue_group_tickets_viewable(self):
        issue_group2 = IssueGroup.objects.create(name="Test Issue Group 2")
        t1 = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test",
            body="Test",
            issue_group=self.issue_group,
        )
        t2 = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test2",
            body="Test2",
            issue_group=self.issue_group,
        )
        t3 = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test2",
            body="Test2",
            issue_group=issue_group2,
        )
        t1.assigned_to.add(self.staff)
        t2.assigned_to.add(self.staff)
        t3.assigned_to.add(self.staff)

        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        displayed_tickets = list(response.context["tickets"].object_list)
        self.assertIn(t1, displayed_tickets)
        self.assertIn(t2, displayed_tickets)
        self.assertNotIn(t3, displayed_tickets)
        self.assertEqual(len(displayed_tickets), 2)

    def test_valid_status_filtering(self):
        issue_group = IssueGroup.objects.create(name="Test Issue Group 3")
        t1 = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="a",
            body="Test",
            issue_group=issue_group,
        )
        t1.assigned_to.add(self.staff)
        t2 = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="b",
            body="Test2",
            issue_group=issue_group,
        )
        t2.assigned_to.add(self.staff)
        t3 = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="c",
            body="Test2",
            issue_group=issue_group,
            status=Ticket.Status.CLOSED,
            closed_reason=Ticket.ClosedReason.ANSWERED,
            closed_at=timezone.now(),
        )
        t3.assigned_to.add(self.staff)
        self.client.login(username=self.staff.username, password="Password123")
        url = reverse(
            "issue_group_detail",
            kwargs={"slug": issue_group.slug},
        )

        response = self.client.get(url, {"status": ""})
        displayed_tickets = list(response.context["tickets"].object_list)
        self.assertIn(t1, displayed_tickets)
        self.assertIn(t2, displayed_tickets)
        self.assertIn(t3, displayed_tickets)

        response = self.client.get(url, {"status": "open"})
        displayed_tickets = list(response.context["tickets"].object_list)
        self.assertIn(t1, displayed_tickets)
        self.assertIn(t2, displayed_tickets)
        self.assertNotIn(t3, displayed_tickets)

        response = self.client.get(url, {"status": "closed"})
        displayed_tickets = list(response.context["tickets"].object_list)
        self.assertEqual([t3], displayed_tickets)

    def test_invalid_status_filtering(self):
        issue_group = IssueGroup.objects.create(name="Test Issue Group 3")
        t1 = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="a",
            body="Test",
            issue_group=issue_group,
        )
        t1.assigned_to.add(self.staff)
        t2 = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="c",
            body="Test2",
            issue_group=issue_group,
            status=Ticket.Status.CLOSED,
            closed_reason=Ticket.ClosedReason.ANSWERED,
            closed_at=timezone.now(),
        )
        t2.assigned_to.add(self.staff)
        self.client.login(username=self.staff.username, password="Password123")
        url = reverse(
            "issue_group_detail",
            kwargs={"slug": issue_group.slug},
        )

        response = self.client.get(url, {"status": "invalid"})
        displayed_tickets = list(response.context["tickets"].object_list)
        self.assertIn(t1, displayed_tickets)
        self.assertIn(t2, displayed_tickets)

    def test_broadcast_empty_message(self):
        self.client.login(username=self.staff.username, password="Password123")
        start_count = IssueUpdate.objects.count()

        response = self.client.post(self.url, {"message": ""}, follow=True)
        self.assertEqual(IssueUpdate.objects.count(), start_count)
        self.assertContains(response, "Unable to broadcast empty message")

    def test_broadcast_message_to_issue_group_with_no_tickets(self):
        self.client.login(username=self.staff.username, password="Password123")
        issue_group = IssueGroup.objects.create(name="Test issue group2")
        response = self.client.get(
            reverse(
                "issue_group_detail",
                kwargs={"slug": issue_group.slug},
            )
        )
        start_count = IssueUpdate.objects.count()
        response = self.client.post(self.url, {"message": "Test message"}, follow=True)
        self.assertEqual(IssueUpdate.objects.count(), start_count)
        self.assertContains(response, "No tickets assigned to issue group")

    def test_successfull_broadcast(self):
        self.client.login(username=self.staff.username, password="Password123")
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="b",
            body="Test2",
            issue_group=self.issue_group,
        )
        ticket.assigned_to.add(self.staff)
        start_count = IssueUpdate.objects.count()
        response = self.client.post(self.url, {"message": "Test message"}, follow=True)
        self.assertEqual(IssueUpdate.objects.count(), start_count + 1)
        self.assertContains(response, "Message broadcasted to issue group.")
