"""Tests for EditTicketView."""

from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from tickets.models.attachment import TicketAttachment
from django.urls import reverse
from tickets.models import Ticket
from django.contrib.auth import get_user_model

User = get_user_model()


class EditTicketViewTest(TestCase):
    """Tests for EditTicketView."""

    def setUp(self):
        self.student = User.objects.create_user(
            username="@editstudent",
            email="edit@test.com",
            password="Password123",
            first_name="Edit",
            last_name="Student",
            user_type="student",
        )
        self.other_student = User.objects.create_user(
            username="@otherstudent",
            email="other@test.com",
            password="Password123",
            first_name="Other",
            last_name="Student",
            user_type="student",
        )
        self.staff = User.objects.create_user(
            username="@editstaff",
            email="editstaff@test.com",
            password="Password123",
            first_name="Staff",
            last_name="User",
            user_type="staff",
        )
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Original subject",
            body="Original body.",
        )
        self.url = reverse("edit_ticket", kwargs={"url_code": self.ticket.url_code})

    def test_student_can_access_edit_page_within_window(self):
        self.client.login(username="@editstudent", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_ticket.html")

    def test_student_can_edit_ticket_within_window(self):
        self.client.login(username="@editstudent", password="Password123")
        response = self.client.post(
            self.url,
            {
                "faculty": "nmes",
                "study_level": "undergraduate",
                "category": "assessment",
                "priority": Ticket.Priority.LOW,
                "subject": "Updated subject",
                "body": "Updated body.",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.subject, "Updated subject")
        self.assertEqual(self.ticket.body, "Updated body.")

    @override_settings(TICKET_EDIT_WINDOW_MINUTES=10)
    def test_student_cannot_edit_after_window(self):
        Ticket.objects.filter(pk=self.ticket.pk).update(
            created_at=timezone.now() - timedelta(minutes=11)
        )
        self.client.login(username="@editstudent", password="Password123")
        response = self.client.get(self.url)
        self.assertRedirects(response, self.ticket.get_absolute_url())

    def test_staff_cannot_access_edit_page(self):
        self.client.login(username="@editstaff", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_other_student_cannot_edit(self):
        self.client.login(username="@otherstudent", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_student_can_add_attachment_when_editing_ticket(self):
        self.client.login(username="@editstudent", password="Password123")

        file = SimpleUploadedFile(
            "extra.pdf",
            b"file content",
            content_type="application/pdf",
        )

        response = self.client.post(
            self.url,
            {
                "faculty": "kbs",
                "study_level": "undergraduate",
                "category": "other",
                "priority": Ticket.Priority.LOW,
                "subject": "Updated subject",
                "body": "Updated body.",
                "attachments": file,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.attachments.count(), 1)

    def test_student_can_remove_attachment_when_editing_ticket(self):
        self.client.login(username="@editstudent", password="Password123")

        attachment = TicketAttachment.objects.create(
            ticket=self.ticket,
            file=SimpleUploadedFile("old.txt", b"old file", content_type="text/plain"),
        )

        response = self.client.post(
            self.url,
            {
                "faculty": "kbs",
                "study_level": "undergraduate",
                "category": "other",
                "priority": "low",
                "subject": "Updated subject",
                "body": "Updated body.",
                "delete_attachments": [str(attachment.pk)],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.attachments.count(), 0)

    def test_student_can_remove_old_and_add_new_attachment_when_editing_ticket(self):
        self.client.login(username="@editstudent", password="Password123")

        old_attachment = TicketAttachment.objects.create(
            ticket=self.ticket,
            file=SimpleUploadedFile("old.txt", b"old file", content_type="text/plain"),
        )
        new_file = SimpleUploadedFile("new.txt", b"new file", content_type="text/plain")

        response = self.client.post(
            self.url,
            {
                "faculty": "kbs",
                "study_level": "undergraduate",
                "category": "other",
                "priority": "low",
                "subject": "Updated subject",
                "body": "Updated body.",
                "delete_attachments": [str(old_attachment.pk)],
                "attachments": new_file,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.attachments.count(), 1)

    @patch("tickets.views.edit_ticket_view.MAX_FILES_PER_TICKET", 1)
    def test_student_cannot_add_attachment_above_max_limit_when_editing(self):
        self.client.login(username="@editstudent", password="Password123")

        existing_attachment = TicketAttachment.objects.create(
            ticket=self.ticket,
            file=SimpleUploadedFile(
                "existing.txt",
                b"existing file content",
                content_type="text/plain",
            ),
        )

        new_file = SimpleUploadedFile(
            "new.txt",
            b"new file content",
            content_type="text/plain",
        )

        response = self.client.post(
            self.url,
            {
                "faculty": "nmes",
                "study_level": "undergraduate",
                "category": "assessment",
                "priority": Ticket.Priority.LOW,
                "subject": "Should not save",
                "body": "Should not save",
                "attachments": [new_file],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_ticket.html")
        self.assertFormError(
            response.context["form"],
            "attachments",
            ["You can upload a maximum of 1 files."],
        )

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.subject, "Original subject")
        self.assertEqual(self.ticket.body, "Original body.")
        self.assertEqual(self.ticket.attachments.count(), 1)
        self.assertTrue(
            TicketAttachment.objects.filter(pk=existing_attachment.pk).exists()
        )
