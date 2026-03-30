from django.test import TestCase, override_settings
from tickets.models import Ticket
from django.contrib.auth import get_user_model

User = get_user_model()


@override_settings(TICKET_STAFF_VISIBILITY_DELAY_MINUTES=0)
class AdminFieldsPermissionsTest(TestCase):
    """Tests for admin (is_superuser) permissions on ticket fields."""

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
