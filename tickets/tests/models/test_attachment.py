from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from tickets.models import Ticket, TicketAttachment, Comment
from clarify.settings import MAX_FILES_PER_TICKET
from django.contrib.auth import get_user_model

User = get_user_model()


class TicketAttachmentTestCase(TestCase):

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.get(username="@janedoe")
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test ticket",
            body="Test body",
        )
        self.comment = Comment.objects.create(
            ticket=self.ticket,
            author=self.student,
            body="Test comment",
        )

    def test_attachment_linked_to_ticket(self):
        file = SimpleUploadedFile(
            "test.pdf", b"content", content_type="application/pdf"
        )
        attachment = TicketAttachment.objects.create(ticket=self.ticket, file=file)
        self.assertEqual(attachment.ticket, self.ticket)
        self.assertIsNone(attachment.comment)

    def test_attachment_linked_to_comment(self):
        file = SimpleUploadedFile(
            "test.pdf", b"content", content_type="application/pdf"
        )
        attachment = TicketAttachment.objects.create(comment=self.comment, file=file)
        self.assertEqual(attachment.comment, self.comment)
        self.assertIsNone(attachment.ticket)

    def test_filename_returns_basename(self):
        file = SimpleUploadedFile(
            "test.pdf", b"content", content_type="application/pdf"
        )
        attachment = TicketAttachment.objects.create(ticket=self.ticket, file=file)
        self.assertTrue(attachment.filename().endswith(".pdf"))

    def test_str_returns_filename(self):
        file = SimpleUploadedFile(
            "test.pdf", b"content", content_type="application/pdf"
        )
        attachment = TicketAttachment.objects.create(ticket=self.ticket, file=file)
        self.assertTrue(str(attachment).endswith(".pdf"))

    def test_max_files_constant(self):
        self.assertEqual(MAX_FILES_PER_TICKET, 5)
