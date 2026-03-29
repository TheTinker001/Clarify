from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from tickets.models import Ticket
from tickets.forms import TicketForm

User = get_user_model()


class CreateTicketViewTest(TestCase):
    """Tests for the ticket view."""

    def setUp(self):
        """Set up test client and users."""
        self.client = Client()
        self.student = User.objects.create_user(
            username="student1",
            email="student1@test.com",
            password="testpass123",
            user_type="student",
        )
        self.staff = User.objects.create_user(
            username="staff1",
            email="staff1@test.com",
            password="testpass123",
            user_type="staff",
        )
        self.url = reverse("create_ticket")
        self.valid_ticket_data = {
            "faculty": "kbs",
            "study_level": "undergraduate",
            "category": "health_and_wellbeing",
            "priority": "high",
            "subject": "Need medical support",
            "body": "I need help with accessing medical services.",
        }

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url)

    def test_redirect_if_staff_user(self):
        self.client.login(username="staff1", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_student_can_access_form(self):
        self.client.login(username="student1", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], TicketForm)

    def test_uses_correct_template(self):
        self.client.login(username="student1", password="testpass123")
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "create_ticket.html")

    def test_create_ticket_with_valid_data(self):
        self.client.login(username="student1", password="testpass123")
        initial_count = Ticket.objects.count()
        response = self.client.post(self.url, self.valid_ticket_data)
        self.assertEqual(Ticket.objects.count(), initial_count + 1)
        self.assertRedirects(response, reverse("dashboard"))
        ticket = Ticket.objects.latest("created_at")
        self.assertEqual(ticket.student, self.student)
        self.assertEqual(ticket.subject, "Need medical support")
        self.assertEqual(ticket.faculty, "kbs")
        self.assertEqual(ticket.status, Ticket.Status.AWAITING_STAFF)

    def test_create_ticket_with_invalid_data(self):
        self.client.login(username="student1", password="testpass123")
        invalid_data = self.valid_ticket_data.copy()
        invalid_data["subject"] = ""
        initial_count = Ticket.objects.count()
        response = self.client.post(self.url, invalid_data)
        self.assertEqual(Ticket.objects.count(), initial_count)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertIn("subject", response.context["form"].errors)

    def test_student_assigned_automatically(self):
        self.client.login(username="student1", password="testpass123")
        self.client.post(self.url, self.valid_ticket_data)
        ticket = Ticket.objects.latest("created_at")
        self.assertEqual(ticket.student, self.student)

    def test_default_status_is_awaiting_staff(self):
        self.client.login(username="student1", password="testpass123")
        self.client.post(self.url, self.valid_ticket_data)
        ticket = Ticket.objects.latest("created_at")
        self.assertEqual(ticket.status, Ticket.Status.AWAITING_STAFF)

    def test_multiple_tickets_by_same_student(self):
        self.client.login(username="student1", password="testpass123")
        self.client.post(self.url, self.valid_ticket_data)
        second_ticket_data = self.valid_ticket_data.copy()
        second_ticket_data["subject"] = "Another issue"
        self.client.post(self.url, second_ticket_data)
        student_tickets = Ticket.objects.filter(student=self.student)
        self.assertEqual(student_tickets.count(), 2)

    def test_staff_cannot_create_ticket_via_post(self):
        self.client.login(username="staff1", password="testpass123")
        initial_count = Ticket.objects.count()
        response = self.client.post(self.url, self.valid_ticket_data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Ticket.objects.count(), initial_count)

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_email_sent_on_ticket_creation(self):
        self.client.login(username="student1", password="testpass123")
        with patch("tickets.helpers.send_mail") as mock_send:
            self.client.post(self.url, self.valid_ticket_data)
            self.assertEqual(mock_send.call_count, 1)

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_ticket_still_created_when_email_fails(self):
        """Ticket is created even if email sending raises an exception (lines 30-31)."""
        self.client.login(username="student1", password="testpass123")
        initial_count = Ticket.objects.count()
        with patch("tickets.helpers.send_mail", side_effect=Exception("SMTP error")):
            response = self.client.post(self.url, self.valid_ticket_data)
            self.assertEqual(Ticket.objects.count(), initial_count + 1)
            self.assertRedirects(response, reverse("dashboard"))

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_success_message_shown_when_email_fails(self):
        """Success message is still shown even if email sending fails."""
        self.client.login(username="student1", password="testpass123")
        with patch("tickets.helpers.send_mail", side_effect=Exception("SMTP error")):
            response = self.client.post(self.url, self.valid_ticket_data, follow=True)
            message_list = list(response.context["messages"])
            self.assertEqual(len(message_list), 1)
            self.assertIn("successfully", str(message_list[0]))

    @override_settings(
        EMAIL_HOST_USER="", EMAIL_HOST_PASSWORD="", DEFAULT_FROM_EMAIL=""
    )
    def test_no_email_sent_without_email_settings(self):
        self.client.login(username="student1", password="testpass123")
        with patch("tickets.helpers.send_mail") as mock_send:
            self.client.post(self.url, self.valid_ticket_data)
            self.assertEqual(mock_send.call_count, 0)

    def test_form_in_context_on_get(self):
        self.client.login(username="student1", password="testpass123")
        response = self.client.get(self.url)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], TicketForm)
        self.assertFalse(response.context["form"].is_bound)

    def test_form_in_context_on_invalid_post(self):
        self.client.login(username="student1", password="testpass123")
        invalid_data = {"subject": ""}
        response = self.client.post(self.url, invalid_data)
        self.assertIn("form", response.context)
        self.assertTrue(response.context["form"].is_bound)
        self.assertFalse(response.context["form"].is_valid())

    def test_create_ticket_with_attachment(self):
        self.client.login(username="student1", password="testpass123")
        file = SimpleUploadedFile(
            "test.pdf", b"content", content_type="application/pdf"
        )
        data = {**self.valid_ticket_data, "attachments": file}
        self.client.post(self.url, data)
        ticket = Ticket.objects.get(subject="Need medical support")
        self.assertEqual(ticket.attachments.count(), 1)

    def test_create_ticket_with_too_many_attachments_is_rejected(self):
        self.client.login(username="student1", password="testpass123")
        files = [
            SimpleUploadedFile(
                f"test{i}.pdf", b"content", content_type="application/pdf"
            )
            for i in range(6)
        ]
        data = {**self.valid_ticket_data, "attachments": files}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ticket.objects.filter(subject="Need medical support").exists())
        self.assertIn("attachments", response.context["form"].errors)
