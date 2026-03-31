"""Tests for comment submission in the ticket detail view."""

from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from tickets.models.attachment import TicketAttachment
from tickets.tests.support import reverse_with_next, valid_comment_post_data
from tickets.models import Comment, Ticket, User


@override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=0)
class CommentViewTestCase(TestCase):
    """Test suite for comment submission via the ticket detail view."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.student2 = User.objects.get(username="@petrapickles")
        self.staff = User.objects.get(username="@janedoe")
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test subject",
            body="Test body.",
        )
        self.ticket.assigned_to.add(self.staff)
        self.unclaimed_ticket = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Unclaimed ticket",
            body="Nobody has claimed this yet.",
        )
        self.url = self.ticket.get_absolute_url()

    def test_get_shows_form_and_comments_in_context(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertIn("comments", response.context)

    def test_no_comments_shows_placeholder_text(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "No comments yet.")

    def test_student_can_comment(self):
        self.client.login(username=self.student.username, password="Password123")
        self.client.post(
            self.url, {"action": "add_comment", "body": "Hello from student."}
        )
        self.assertEqual(Comment.objects.filter(ticket=self.ticket).count(), 1)
        comment = Comment.objects.get(ticket=self.ticket)
        self.assertEqual(comment.author, self.student)
        self.assertEqual(comment.body, "Hello from student.")

    def test_student_comment_redirects_after_post(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(
            self.url, {"action": "add_comment", "body": "Hello from student."}
        )
        self.assertRedirects(response, self.url)

    def test_staff_can_comment_on_claimed_ticket(self):
        self.client.login(username=self.staff.username, password="Password123")
        self.client.post(
            self.url, {"action": "add_comment", "body": "Hello from staff."}
        )
        self.assertEqual(Comment.objects.filter(ticket=self.ticket).count(), 1)
        comment = Comment.objects.get(ticket=self.ticket)
        self.assertEqual(comment.author, self.staff)
        self.assertEqual(comment.body, "Hello from staff.")

    def test_staff_comment_redirects_after_post(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(
            self.url, {"action": "add_comment", "body": "Hello from staff."}
        )
        self.assertRedirects(response, self.url)

    def test_staff_cannot_comment_on_unclaimed_ticket(self):
        self.client.login(username=self.staff.username, password="Password123")
        unclaimed_url = self.unclaimed_ticket.get_absolute_url()
        response = self.client.post(
            unclaimed_url, {"action": "add_comment", "body": "Trying to comment."}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            Comment.objects.filter(ticket=self.unclaimed_ticket).count(), 0
        )

    def test_non_owner_student_cannot_comment(self):
        self.client.login(username=self.student2.username, password="Password123")
        response = self.client.post(
            self.url, {"action": "add_comment", "body": "Sneaky comment."}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Comment.objects.filter(ticket=self.ticket).count(), 0)

    def test_unauthenticated_cannot_comment(self):
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.post(
            self.url, {"action": "add_comment", "body": "Anonymous comment."}
        )
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )

    def test_invalid_comment_rerenders_form_with_errors(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(self.url, {"action": "add_comment", "body": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ticket_detail.html")
        self.assertFalse(response.context["form"].is_valid())
        self.assertEqual(Comment.objects.filter(ticket=self.ticket).count(), 0)

    def test_student_can_submit_multiple_consecutive_comments(self):
        self.client.login(username=self.student.username, password="Password123")
        self.client.post(self.url, {"action": "add_comment", "body": "First comment."})
        self.client.post(self.url, {"action": "add_comment", "body": "Second comment."})
        self.client.post(self.url, {"action": "add_comment", "body": "Third comment."})
        self.assertEqual(Comment.objects.filter(ticket=self.ticket).count(), 3)

    def test_staff_can_submit_multiple_consecutive_comments(self):
        self.client.login(username=self.staff.username, password="Password123")
        self.client.post(
            self.url, {"action": "add_comment", "body": "First staff comment."}
        )
        self.client.post(
            self.url, {"action": "add_comment", "body": "Second staff comment."}
        )
        self.assertEqual(Comment.objects.filter(ticket=self.ticket).count(), 2)

    def test_comments_displayed_in_template(self):
        Comment.objects.create(
            ticket=self.ticket, author=self.student, body="Student comment here."
        )
        Comment.objects.create(
            ticket=self.ticket, author=self.staff, body="Staff comment here."
        )
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "Student comment here.")
        self.assertContains(response, "Staff comment here.")

    def test_student_comments_have_blue_styling(self):
        Comment.objects.create(
            ticket=self.ticket, author=self.student, body="Student comment."
        )
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "comment-card--student")

    def test_staff_comments_have_red_styling(self):
        Comment.objects.create(
            ticket=self.ticket, author=self.staff, body="Staff comment."
        )
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "comment-card--staff")

    def test_comment_form_shown_to_student(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "Add a comment")

    def test_comment_form_shown_to_staff_on_claimed_ticket(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "Add a comment")

    def test_comment_form_not_shown_to_staff_on_unclaimed_ticket(self):
        self.client.login(username=self.staff.username, password="Password123")
        unclaimed_url = self.unclaimed_ticket.get_absolute_url()
        response = self.client.get(unclaimed_url)
        self.assertNotContains(response, "Add a comment")

    def test_other_staff_cannot_comment_on_claimed_ticket(self):
        other_staff = User.objects.get(username="@jonrain")
        self.client.login(username=other_staff.username, password="Password123")
        response = self.client.post(self.url, {"action": "add_comment", "body": "Nope"})
        self.assertEqual(response.status_code, 404)

    def test_unknown_action_returns_404(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(
            self.url, {"action": "imaginary_action", "body": "Hi"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Comment.objects.filter(ticket=self.ticket).count(), 0)

    def test_student_can_comment_with_attachment(self):
        self.client.login(username=self.student.username, password="Password123")
        file = SimpleUploadedFile(
            "test.pdf", b"content", content_type="application/pdf"
        )
        self.client.post(
            self.url,
            {
                "action": "add_comment",
                "body": "Comment with file.",
                "attachments": file,
            },
        )
        self.assertEqual(Comment.objects.filter(ticket=self.ticket).count(), 1)
        comment = Comment.objects.get(ticket=self.ticket)
        self.assertEqual(comment.attachments.count(), 1)

    def test_staff_can_comment_with_attachment(self):
        self.client.login(username=self.staff.username, password="Password123")
        file = SimpleUploadedFile(
            "test.pdf", b"content", content_type="application/pdf"
        )
        self.client.post(
            self.url,
            {
                "action": "add_comment",
                "body": "Staff comment with file.",
                "attachments": file,
            },
        )
        comment = Comment.objects.get(ticket=self.ticket)
        self.assertEqual(comment.attachments.count(), 1)

    def test_comment_with_exactly_five_attachments_is_accepted(self):
        self.client.login(username=self.student.username, password="Password123")
        files = [
            SimpleUploadedFile(
                f"test{i}.pdf", b"content", content_type="application/pdf"
            )
            for i in range(5)
        ]
        response = self.client.post(
            self.url,
            {"action": "add_comment", "body": "Five files.", "attachments": files},
        )
        self.assertRedirects(response, self.url)
        comment = Comment.objects.get(ticket=self.ticket)
        self.assertEqual(comment.attachments.count(), 5)

    def test_comment_with_more_than_five_attachments_is_rejected(self):
        self.client.login(username=self.student.username, password="Password123")
        files = [
            SimpleUploadedFile(
                f"test{i}.pdf", b"content", content_type="application/pdf"
            )
            for i in range(6)
        ]
        response = self.client.post(
            self.url,
            {"action": "add_comment", "body": "Too many files.", "attachments": files},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.filter(ticket=self.ticket).count(), 0)
        self.assertIn("attachments", response.context["form"].errors)
        self.assertIn(
            "You can upload a maximum of 5 files.",
            response.context["form"].errors["attachments"][0],
        )

    def test_comment_with_invalid_file_type_is_rejected(self):
        self.client.login(username=self.student.username, password="Password123")
        file = SimpleUploadedFile(
            "test.exe", b"content", content_type="application/exe"
        )
        response = self.client.post(
            self.url,
            {"action": "add_comment", "body": "Bad file.", "attachments": file},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.filter(ticket=self.ticket).count(), 0)
        self.assertIn("attachments", response.context["form"].errors)

    def test_comment_with_large_file_is_rejected(self):
        self.client.login(username=self.student.username, password="Password123")
        file = SimpleUploadedFile(
            "large.pdf", b"x" * (6 * 1024 * 1024), content_type="application/pdf"
        )
        response = self.client.post(
            self.url,
            {"action": "add_comment", "body": "Large file.", "attachments": file},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.filter(ticket=self.ticket).count(), 0)
        self.assertIn("attachments", response.context["form"].errors)

    def test_attachment_link_displayed_in_comment(self):
        comment = Comment.objects.create(
            ticket=self.ticket, author=self.student, body="Comment with attachment."
        )
        file = SimpleUploadedFile(
            "test.pdf", b"content", content_type="application/pdf"
        )
        TicketAttachment.objects.create(comment=comment, file=file)
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "ticket_attachments")
        self.assertContains(response, ".pdf")

    def test_student_comment_on_closed_ticket_reopens_ticket(self):
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.ticket.closed_at = timezone.now()
        self.ticket.awaiting_student_since = timezone.now() - timedelta(days=2)
        self.ticket.save()

        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(
            self.url,
            data=valid_comment_post_data("Student follow-up"),
        )

        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.AWAITING_STAFF)
        self.assertIsNone(self.ticket.closed_reason)
        self.assertIsNone(self.ticket.closed_at)
        self.assertIsNone(self.ticket.awaiting_student_since)

    def test_staff_comment_sets_ticket_to_awaiting_student(self):
        self.ticket.status = Ticket.Status.AWAITING_STAFF
        self.ticket.awaiting_student_since = None
        self.ticket.save()

        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(
            self.url,
            data=valid_comment_post_data("Staff reply"),
        )

        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.AWAITING_STUDENT)
        self.assertIsNotNone(self.ticket.awaiting_student_since)

    def test_student_comment_sets_ticket_to_awaiting_staff(self):
        self.ticket.status = Ticket.Status.AWAITING_STUDENT
        self.ticket.awaiting_student_since = timezone.now() - timedelta(days=2)
        self.ticket.save()

        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(
            self.url,
            data=valid_comment_post_data("Student reply"),
        )

        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.AWAITING_STAFF)
        self.assertIsNone(self.ticket.awaiting_student_since)

    def test_success_message_shown_after_comment(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(
            self.url,
            data=valid_comment_post_data("Student reply"),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        messages = list(response.context["messages"])
        self.assertTrue(any("Comment added." in str(m) for m in messages))
