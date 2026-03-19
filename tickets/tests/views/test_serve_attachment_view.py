import os
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from tickets.models import Ticket
from tickets.models.attachment import TicketAttachment
from tickets.models.comment import Comment
from tickets.tests.helpers import _reverse_with_next

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ServeAttachmentViewTest(TestCase):
    """Tests for ServeAttachmentView — covers all access-control branches."""

    def setUp(self):
        self.student = User.objects.create_user(
            username="student1",
            email="student1@test.com",
            password="Password123",
            user_type="student",
        )
        self.other_student = User.objects.create_user(
            username="student2",
            email="student2@test.com",
            password="Password123",
            user_type="student",
        )
        self.staff = User.objects.create_user(
            username="staff1",
            email="staff1@test.com",
            password="Password123",
            user_type="staff",
        )
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test ticket",
            body="Test body.",
        )
        file = SimpleUploadedFile("test.pdf", b"pdf content", content_type="application/pdf")
        self.attachment = TicketAttachment.objects.create(ticket=self.ticket, file=file)
        # file.name is e.g. "ticket_attachments/2026/03/19/test.pdf"; strip the prefix
        self.path = self.attachment.file.name.removeprefix("ticket_attachments/")
        self.url = reverse("serve_attachment", kwargs={"path": self.path})

    # --- Case 1: unauthenticated ---

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            _reverse_with_next("log_in", self.url),
            fetch_redirect_response=False,
        )

    # --- Case 2: staff ---

    def test_staff_can_access_any_attachment(self):
        self.client.login(username="staff1", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # --- Case 3: student who owns the ticket ---

    def test_ticket_owner_student_can_access_attachment(self):
        self.client.login(username="student1", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # --- Case 4: different student (not the owner) ---

    def test_non_owner_student_gets_404(self):
        self.client.login(username="student2", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    # --- Case 5: attachment not found in DB ---

    def test_nonexistent_path_returns_404(self):
        self.client.login(username="staff1", password="Password123")
        url = reverse("serve_attachment", kwargs={"path": "2000/01/01/ghost.pdf"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # --- Case 6: file missing from disk ---

    def test_missing_file_on_disk_raises(self):
        self.client.login(username="staff1", password="Password123")
        os.remove(self.attachment.file.path)
        with self.assertRaises(FileNotFoundError):
            self.client.get(self.url)

    # --- Case 7: attachment linked to a comment ---

    def test_comment_attachment_owner_student_gets_200(self):
        comment = Comment.objects.create(
            ticket=self.ticket,
            author=self.student,
            body="Comment with attachment.",
        )
        file = SimpleUploadedFile("comment.pdf", b"pdf content", content_type="application/pdf")
        comment_attachment = TicketAttachment.objects.create(comment=comment, file=file)
        path = comment_attachment.file.name.removeprefix("ticket_attachments/")
        url = reverse("serve_attachment", kwargs={"path": path})
        self.client.login(username="student1", password="Password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_non_owner_student_cannot_access_comment_attachment(self):
        comment = Comment.objects.create(
            ticket=self.ticket,
            author=self.student,
            body="Comment with attachment.",
        )
        file = SimpleUploadedFile("comment.pdf", b"pdf content", content_type="application/pdf")
        comment_attachment = TicketAttachment.objects.create(comment=comment, file=file)
        path = comment_attachment.file.name.removeprefix("ticket_attachments/")
        url = reverse("serve_attachment", kwargs={"path": path})
        self.client.login(username="student2", password="Password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # --- Case 8: attachment with neither ticket nor comment ---

    def test_orphan_attachment_returns_404_for_student(self):
        file = SimpleUploadedFile("orphan.pdf", b"pdf content", content_type="application/pdf")
        orphan = TicketAttachment.objects.create(file=file)
        path = orphan.file.name.removeprefix("ticket_attachments/")
        url = reverse("serve_attachment", kwargs={"path": path})
        self.client.login(username="student1", password="Password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # --- user_type is neither staff nor student ---

    def test_unknown_user_type_gets_404(self):
        User.objects.create_user(
            username="other1",
            email="other1@test.com",
            password="Password123",
            user_type="other",
        )
        self.client.login(username="other1", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
