"""Tests for admin (is_superuser) permissions on ticket priority and fields."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tickets.models import Ticket

User = get_user_model()


class AdminPriorityPermissionsTest(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username="@admstudent",
            email="admstudent@test.com",
            password="Password123",
            user_type="student",
        )
        self.staff = User.objects.create_user(
            username="@admstaff",
            email="admstaff@test.com",
            password="Password123",
            user_type="staff",
            faculties="kbs",
            study_levels="undergraduate",
            categories="other",
        )
        self.admin = User.objects.create_user(
            username="@admadmin",
            email="admadmin@test.com",
            password="Password123",
            user_type="staff",
            is_superuser=True,
            faculties="kbs",
            study_levels="undergraduate",
            categories="other",
        )
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Test",
            body="Body.",
        )
        self.ticket.assigned_to.add(self.admin)
        self.url = self.ticket.get_absolute_url()

    def test_admin_can_set_priority(self):
        self.client.login(username="@admadmin", password="Password123")
        response = self.client.post(
            self.url,
            {
                "action": "set_priority",
                "priority": "high",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.priority, "high")

    def test_normal_staff_cannot_set_priority(self):
        self.ticket.assigned_to.set([self.staff])
        self.client.login(username="@admstaff", password="Password123")
        response = self.client.post(
            self.url,
            {
                "action": "set_priority",
                "priority": "high",
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_student_cannot_set_priority(self):
        self.client.login(username="@admstudent", password="Password123")
        response = self.client.post(
            self.url,
            {
                "action": "set_priority",
                "priority": "high",
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_sees_priority_form(self):
        self.client.login(username="@admadmin", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["ticket_priority_form"])

    def test_normal_staff_does_not_see_priority_form(self):
        self.ticket.assigned_to.set([self.staff])
        self.client.login(username="@admstaff", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["ticket_priority_form"])


class AdminFieldsPermissionsTest(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username="@fldstudent",
            email="fldstudent@test.com",
            password="Password123",
            user_type="student",
        )
        self.staff = User.objects.create_user(
            username="@fldstaff",
            email="fldstaff@test.com",
            password="Password123",
            user_type="staff",
            faculties="kbs,nmes",
            study_levels="undergraduate",
            categories="other,assessment",
        )
        self.admin = User.objects.create_user(
            username="@fldadmin",
            email="fldadmin@test.com",
            password="Password123",
            user_type="staff",
            is_superuser=True,
            faculties="kbs,nmes",
            study_levels="undergraduate",
            categories="other,assessment",
        )
        self.ticket = Ticket.objects.create(
            student=self.student,
            faculty="kbs",
            study_level="undergraduate",
            category="other",
            subject="Test",
            body="Body.",
        )
        self.ticket.assigned_to.add(self.admin)
        self.url = self.ticket.get_absolute_url()

    def test_admin_can_edit_ticket_fields(self):
        self.client.login(username="@fldadmin", password="Password123")
        response = self.client.post(
            self.url,
            {
                "action": "set_ticket_fields",
                "faculty": "nmes",
                "study_level": "undergraduate",
                "category": "assessment",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.faculty, "nmes")
        self.assertEqual(self.ticket.category, "assessment")

    def test_normal_staff_cannot_edit_ticket_fields(self):
        self.ticket.assigned_to.set([self.staff])
        self.client.login(username="@fldstaff", password="Password123")
        response = self.client.post(
            self.url,
            {
                "action": "set_ticket_fields",
                "faculty": "nmes",
                "study_level": "undergraduate",
                "category": "assessment",
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_student_cannot_edit_ticket_fields(self):
        self.client.login(username="@fldstudent", password="Password123")
        response = self.client.post(
            self.url,
            {
                "action": "set_ticket_fields",
                "faculty": "nmes",
                "study_level": "undergraduate",
                "category": "assessment",
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_cannot_edit_ticket_fields_if_not_assigned(self):
        self.ticket.assigned_to.clear()
        self.client.login(username="@fldadmin", password="Password123")

        response = self.client.post(
            self.url,
            {
                "action": "set_ticket_fields",
                "faculty": "nmes",
                "study_level": "undergraduate",
                "category": "assessment",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_admin_sees_fields_form(self):
        self.client.login(username="@fldadmin", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["ticket_fields_form"])

    def test_normal_staff_does_not_see_fields_form(self):
        self.ticket.assigned_to.set([self.staff])
        self.client.login(username="@fldstaff", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get("ticket_fields_form"))
