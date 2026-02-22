"""Tests for the ticket detail view."""

from django.test import TestCase, override_settings
from unittest.mock import patch
from tickets.models import Ticket, User
from tickets.models.ticket_response import TicketResponse
from tickets.forms.ticket_response_form import TicketResponseForm
from tickets.tests.helpers import MenuTesterMixin, reverse_with_next


class TicketDetailViewTestCase(TestCase, MenuTesterMixin):
    """Test suite for the ticket detail view."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.student2 = User.objects.get(username="@petrapickles")
        self.staff = User.objects.get(username="@janedoe")
        self.staff.user_type = User.USER_TYPE_STAFF
        self.staff.save()
        self.ticket = Ticket.objects.create(
            student=self.student,
            assigned_to=self.staff,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Update card access",
            body="Card access not working for lab.",
        )
        self.url = self.ticket.get_absolute_url()

    def test_ticket_detail_url(self):
        self.assertEqual(self.url, f"/ticket/{self.ticket.url_code}/")

    def test_get_ticket_detail_redirects_when_not_logged_in(self):
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )

    def test_get_ticket_detail(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ticket_detail.html")
        self.assertEqual(response.context["ticket"], self.ticket)
        self.assertContains(response, self.ticket.subject)
        self.assertContains(response, self.ticket.body)
        self.assert_menu(response)

    def test_ticket_detail_returns_404_for_missing_ticket(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get("/ticket/jujutsu/")
        self.assertEqual(response.status_code, 404)

    def test_user_is_not_owner_nor_staff(self):
        self.client.login(username=self.student2.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_get_ticket_detail_contains_response_form(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], TicketResponseForm)

    def test_get_ticket_detail_shows_existing_responses(self):
        TicketResponse.objects.create(
            ticket=self.ticket, author=self.staff, body="Staff response here."
        )
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff response here.")

    def test_staff_can_respond_to_ticket(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(
            self.url, {"body": "Here is your answer."}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TicketResponse.objects.count(), 1)
        resp_obj = TicketResponse.objects.first()
        self.assertEqual(resp_obj.body, "Here is your answer.")
        self.assertEqual(resp_obj.author, self.staff)
        self.assertEqual(resp_obj.ticket, self.ticket)

    def test_staff_response_changes_status_to_awaiting_student(self):
        self.client.login(username=self.staff.username, password="Password123")
        self.client.post(self.url, {"body": "Here is your answer."})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.AWAITING_STUDENT)

    def test_student_can_respond_to_ticket(self):
        self.ticket.status = Ticket.Status.AWAITING_STUDENT
        self.ticket.save()
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(
            self.url, {"body": "Thanks, but I have a follow-up."}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TicketResponse.objects.count(), 1)
        resp_obj = TicketResponse.objects.first()
        self.assertEqual(resp_obj.author, self.student)

    def test_student_response_changes_status_to_awaiting_staff(self):
        self.ticket.status = Ticket.Status.AWAITING_STUDENT
        self.ticket.save()
        self.client.login(username=self.student.username, password="Password123")
        self.client.post(self.url, {"body": "Follow-up question."})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.AWAITING_STAFF)

    def test_empty_response_body_is_rejected(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(self.url, {"body": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TicketResponse.objects.count(), 0)
        self.assertIn("form", response.context)
        self.assertTrue(response.context["form"].errors)

    def test_staff_response_redirects_to_ticket_detail(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(self.url, {"body": "Answer."})
        self.assertRedirects(response, self.url)

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
        SITE_URL="http://testserver",
    )
    def test_email_sent_to_student_when_staff_responds(self):
        self.client.login(username=self.staff.username, password="Password123")
        with patch("tickets.helpers.send_mail") as mock_send:
            self.client.post(self.url, {"body": "Here is your answer."})
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args.kwargs
            self.assertIn(self.student.email, call_kwargs["recipient_list"])
            self.assertIn("Update card access", call_kwargs["subject"])
            self.assertIn(self.ticket.url_code, call_kwargs["message"])
            self.assertIn("Here is your answer.", call_kwargs["message"])

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_no_email_sent_when_student_responds(self):
        self.ticket.status = Ticket.Status.AWAITING_STUDENT
        self.ticket.save()
        self.client.login(username=self.student.username, password="Password123")
        with patch("tickets.helpers.send_mail") as mock_send:
            self.client.post(self.url, {"body": "Follow-up."})
            mock_send.assert_not_called()

    @override_settings(
        EMAIL_HOST_USER="clarify@example.com",
        EMAIL_HOST_PASSWORD="app-password",
        DEFAULT_FROM_EMAIL="clarify@example.com",
    )
    def test_ticket_still_saved_when_email_fails(self):
        self.client.login(username=self.staff.username, password="Password123")
        with patch("tickets.helpers.send_mail", side_effect=Exception("SMTP fail")):
            response = self.client.post(
                self.url, {"body": "Answer."}, follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(TicketResponse.objects.count(), 1)

    def test_no_email_sent_without_email_settings(self):
        self.client.login(username=self.staff.username, password="Password123")
        with patch("tickets.helpers.send_mail") as mock_send:
            self.client.post(self.url, {"body": "Answer."})
            mock_send.assert_not_called()

    def test_responses_context_is_passed(self):
        TicketResponse.objects.create(
            ticket=self.ticket, author=self.staff, body="First response."
        )
        TicketResponse.objects.create(
            ticket=self.ticket, author=self.student, body="Student follow-up."
        )
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["responses"]), 2)
