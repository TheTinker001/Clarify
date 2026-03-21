"""Tests for the Internal Notes feature on the ticket detail view."""

from django.test import TestCase
from django.urls import reverse

from tickets.models import Ticket, User


class TicketInternalNotesTestCase(TestCase):
    """Test suite for the staff-only internal notes on a ticket."""

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
            faculty="nmes",
            study_level="undergraduate",
            category="other",
            subject="Test subject",
            body="Test body.",
        )
        self.ticket.assigned_to.add(self.staff)
        self.url = reverse("ticket_detail", kwargs={"url_code": self.ticket.url_code})
        self.edit_url = reverse(
            "internal_note_edit", kwargs={"url_code": self.ticket.url_code}
        )

    #  Ticket detail: visibility

    def test_staff_sees_internal_notes_section(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "Internal Notes")

    def test_student_cannot_see_internal_notes_section(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertNotContains(response, "Internal Notes")

    def test_claiming_staff_sees_edit_button(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, self.edit_url)

    def test_other_staff_does_not_see_edit_button(self):
        self.client.login(username=self.other_staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertNotContains(response, self.edit_url)

    def test_staff_sees_note_text_when_present(self):
        self.ticket.internal_notes = "A secret staff note."
        self.ticket.save(update_fields=["internal_notes"])
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "A secret staff note.")

    def test_student_cannot_see_note_text(self):
        self.ticket.internal_notes = "A secret staff note."
        self.ticket.save(update_fields=["internal_notes"])
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.url)
        self.assertNotContains(response, "A secret staff note.")

    def test_staff_sees_empty_state_when_no_notes(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertContains(response, "No internal notes yet.")

    def test_can_edit_internal_notes_true_for_claiming_staff(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertTrue(response.context["can_edit_internal_notes"])

    def test_can_edit_internal_notes_false_for_other_staff(self):
        self.client.login(username=self.other_staff.username, password="Password123")
        response = self.client.get(self.url)
        self.assertFalse(response.context["can_edit_internal_notes"])

    # Edit page: access

    def test_claiming_staff_can_get_edit_page(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "internal_note_edit.html")

    def test_other_staff_gets_404_on_edit_page(self):
        self.client.login(username=self.other_staff.username, password="Password123")
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 404)

    def test_student_gets_404_on_edit_page(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_redirected_from_edit_page(self):
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/log_in/", response["Location"])

    # Edit page: POST

    def test_claiming_staff_can_save_internal_notes(self):
        self.client.login(username=self.staff.username, password="Password123")
        self.client.post(self.edit_url, {"internal_notes": "Updated note."})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.internal_notes, "Updated note.")

    def test_save_redirects_to_ticket_detail(self):
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.post(self.edit_url, {"internal_notes": "Updated note."})
        self.assertRedirects(response, self.url)

    def test_claiming_staff_can_save_empty_notes(self):
        self.ticket.internal_notes = "Existing note."
        self.ticket.save(update_fields=["internal_notes"])
        self.client.login(username=self.staff.username, password="Password123")
        self.client.post(self.edit_url, {"internal_notes": ""})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.internal_notes, "")

    def test_other_staff_cannot_post_to_edit_page(self):
        self.client.login(username=self.other_staff.username, password="Password123")
        response = self.client.post(self.edit_url, {"internal_notes": "Hacked."})
        self.assertEqual(response.status_code, 404)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.internal_notes, "")

    def test_student_cannot_post_to_edit_page(self):
        self.client.login(username=self.student.username, password="Password123")
        response = self.client.post(self.edit_url, {"internal_notes": "Hacked."})
        self.assertEqual(response.status_code, 404)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.internal_notes, "")

    def test_unauthenticated_post_redirects(self):
        response = self.client.post(self.edit_url, {"internal_notes": "Anon."})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/log_in/", response["Location"])
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.internal_notes, "")

    # Edit page: form prefilling

    def test_edit_page_prefills_existing_internal_notes(self):
        self.ticket.internal_notes = "Existing note."
        self.ticket.save(update_fields=["internal_notes"])
        self.client.login(username=self.staff.username, password="Password123")
        response = self.client.get(self.edit_url)
        self.assertContains(response, "Existing note.")

    # URL resolution

    def test_internal_note_edit_url_resolves(self):
        self.assertEqual(
            reverse("internal_note_edit", kwargs={"url_code": self.ticket.url_code}),
            f"/ticket/{self.ticket.url_code}/internal-notes",
        )
