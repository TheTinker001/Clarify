"""Tests for the Internal Notes feature on the ticket detail view."""

from django.test import TestCase
from django.urls import reverse

from tickets.models import InternalNote, Ticket, User


class InternalNoteViewTestCase(TestCase):
    """Test suite for staff-only internal notes on a ticket."""

    fixtures = [
        "tickets/tests/fixtures/default_user.json",
        "tickets/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.student = User.objects.get(username="@johndoe")
        self.staff = User.objects.get(username="@janedoe")
        self.other_staff = User.objects.get(username="@jonrain")
        self.ticket = Ticket.objects.create(
            student=self.student,
            assigned_to=self.staff,
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test subject",
            body="Test body.",
        )
        self.url = reverse("ticket_detail", kwargs={"url_code": self.ticket.url_code})

    # Template visibility

    def test_staff_can_see_internal_notes_section(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "Internal Notes")
        self.assertContains(response, "add_internal_note")

    def test_student_cannot_see_internal_notes_section(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertNotContains(response, "Internal Notes")
        self.assertNotContains(response, "add_internal_note")

    def test_staff_sees_existing_notes(self):
        InternalNote.objects.create(
            ticket=self.ticket,
            author=self.staff,
            body="A secret staff note.",
        )
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "A secret staff note.")

    def test_staff_sees_empty_state_when_no_notes(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "No internal notes yet.")

    # Successful note submission

    def test_staff_can_add_internal_note(self):
        self.client.login(username=self.staff.username, password="Password123")
        self.client.post(self.url, {"action": "add_internal_note", "body": "Staff note."})
        self.assertEqual(InternalNote.objects.count(), 1)
        note = InternalNote.objects.first()
        self.assertEqual(note.body, "Staff note.")
        self.assertEqual(note.author, self.staff)
        self.assertEqual(note.ticket, self.ticket)

    def test_add_note_redirects_to_ticket_detail(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(
            self.url, {"action": "add_internal_note", "body": "Staff note."}
        )
        self.assertRedirects(response, self.url)

    def test_add_note_shows_success_message(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(
            self.url,
            {"action": "add_internal_note", "body": "Staff note."},
            follow=True,
        )
        self.assertContains(response, "Internal note added.")

    def test_any_staff_member_can_add_note(self):
        self.client.login(username=self.other_staff.username, password="Password123")
        self.client.post(self.url, {"action": "add_internal_note", "body": "Other staff note."})
        self.assertEqual(InternalNote.objects.count(), 1)
        self.assertEqual(InternalNote.objects.first().author, self.other_staff)

    # Access control

    def test_student_cannot_add_internal_note(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(
            self.url, {"action": "add_internal_note", "body": "Sneaky note."}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(InternalNote.objects.count(), 0)

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.post(
            self.url, {"action": "add_internal_note", "body": "Anonymous note."}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/log_in/", response["Location"])

    # Invalid form handling

    def test_blank_body_rerenders_form(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(
            self.url, {"action": "add_internal_note", "body": ""}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ticket_detail.html")
        self.assertEqual(InternalNote.objects.count(), 0)

    def test_body_too_long_rerenders_form(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(
            self.url, {"action": "add_internal_note", "body": "x" * 5001}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ticket_detail.html")
        self.assertEqual(InternalNote.objects.count(), 0)

    # Model

    def test_str_representation(self):
        note = InternalNote.objects.create(
            ticket=self.ticket,
            author=self.staff,
            body="A note.",
        )
        self.assertEqual(str(note), f"Internal note by {self.staff} on Ticket {self.ticket.pk}")
