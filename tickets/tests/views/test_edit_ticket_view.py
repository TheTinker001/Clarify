"""Tests for the edit/delete ticket views and 15-minute staff visibility."""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from tickets.models import Ticket

User = get_user_model()


class EditTicketViewTest(TestCase):

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


class DeleteTicketViewTest(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username="@delstudent",
            email="del@test.com",
            password="Password123",
            first_name="Del",
            last_name="Student",
            user_type="student",
        )
        self.other_student = User.objects.create_user(
            username="@delother",
            email="delother@test.com",
            password="Password123",
            first_name="Other",
            last_name="Student",
            user_type="student",
        )
        self.staff = User.objects.create_user(
            username="@delstaff",
            email="delstaff@test.com",
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
            subject="To delete",
            body="Body.",
        )
        self.url = reverse("delete_ticket", kwargs={"url_code": self.ticket.url_code})

    def test_student_can_delete_within_window(self):
        self.client.login(username="@delstudent", password="Password123")
        response = self.client.post(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Ticket.objects.filter(pk=self.ticket.pk).count(), 0)

    @override_settings(TICKET_EDIT_WINDOW_MINUTES=10)
    def test_student_cannot_delete_after_window(self):
        Ticket.objects.filter(pk=self.ticket.pk).update(
            created_at=timezone.now() - timedelta(minutes=11)
        )
        self.client.login(username="@delstudent", password="Password123")
        response = self.client.post(self.url)
        self.assertRedirects(response, self.ticket.get_absolute_url())
        self.assertEqual(Ticket.objects.filter(pk=self.ticket.pk).count(), 1)

    def test_staff_cannot_delete(self):
        self.client.login(username="@delstaff", password="Password123")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_other_student_cannot_delete(self):
        self.client.login(username="@delother", password="Password123")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)

    def test_get_not_allowed(self):
        self.client.login(username="@delstudent", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_redirects_to_dashboard_after_delete(self):
        self.client.login(username="@delstudent", password="Password123")
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("dashboard"))


class StaffVisibilityDelayTest(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username="@visstudent",
            email="vis@test.com",
            password="Password123",
            first_name="Vis",
            last_name="Student",
            user_type="student",
        )
        self.staff = User.objects.create_user(
            username="@visstaff",
            email="visstaff@test.com",
            password="Password123",
            first_name="Staff",
            last_name="User",
            user_type="staff",
            faculties="kbs",
            study_levels="undergraduate",
            categories="other",
        )
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="New ticket",
            body="Body.",
        )

    @override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=15)
    def test_staff_cannot_view_ticket_before_15_minutes(self):
        self.client.login(username="@visstaff", password="Password123")
        url = self.ticket.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=15)
    def test_staff_can_view_ticket_after_15_minutes(self):
        Ticket.objects.filter(pk=self.ticket.pk).update(
            created_at=timezone.now() - timedelta(minutes=16)
        )
        self.client.login(username="@visstaff", password="Password123")
        url = self.ticket.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_student_can_always_view_own_ticket(self):
        self.client.login(username="@visstudent", password="Password123")
        url = self.ticket.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=15)
    def test_staff_dashboard_hides_new_tickets(self):
        self.client.login(username="@visstaff", password="Password123")
        response = self.client.get(reverse("dashboard"), {"tab": "open_tickets"})
        self.assertEqual(response.status_code, 200)
        tickets_shown = response.context["page_obj"].object_list
        self.assertEqual(len(tickets_shown), 0)

    @override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=15)
    def test_staff_dashboard_shows_old_tickets(self):
        Ticket.objects.filter(pk=self.ticket.pk).update(
            created_at=timezone.now() - timedelta(minutes=16)
        )
        self.client.login(username="@visstaff", password="Password123")
        response = self.client.get(reverse("dashboard"), {"tab": "open_tickets"})
        self.assertEqual(response.status_code, 200)
        tickets_shown = response.context["page_obj"].object_list
        self.assertEqual(len(tickets_shown), 1)


class TicketModelHelpersTest(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username="@modelstudent",
            email="model@test.com",
            password="Password123",
            user_type="student",
        )

    @override_settings(TICKET_EDIT_WINDOW_MINUTES=10)
    def test_is_editable_by_student_within_window(self):
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Test",
            body="Body.",
        )
        self.assertTrue(ticket.is_editable_by_student())

    @override_settings(TICKET_EDIT_WINDOW_MINUTES=10)
    def test_is_not_editable_after_window(self):
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Test",
            body="Body.",
        )
        Ticket.objects.filter(pk=ticket.pk).update(
            created_at=timezone.now() - timedelta(minutes=11)
        )
        ticket.refresh_from_db()
        self.assertFalse(ticket.is_editable_by_student())

    @override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=15)
    def test_is_visible_to_staff_after_delay(self):
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Test",
            body="Body.",
        )
        Ticket.objects.filter(pk=ticket.pk).update(
            created_at=timezone.now() - timedelta(minutes=16)
        )
        ticket.refresh_from_db()
        self.assertTrue(ticket.is_visible_to_staff())

    @override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=15)
    def test_is_not_visible_to_staff_before_delay(self):
        ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Test",
            body="Body.",
        )
        self.assertFalse(ticket.is_visible_to_staff())
