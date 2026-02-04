"""Tests of dashboard view."""

from django.contrib.auth.hashers import check_password
from django.test import TestCase
from django.urls import reverse
from tickets.models import User
from tickets.tests.helpers import LogInTester


class DashboardViewTestCase(TestCase, LogInTester):
    """Tests of the dashboard view."""

    fixtures = ["tickets/tests/fixtures/default_user.json"]

    def setUp(self):
        self.url = reverse("dashboard")
        self.form_input = {
            "first_name": "Jane",
            "last_name": "Doe",
            "username": "@janedoe",
            "email": "janedoe@example.org",
            "user_type": User.USER_TYPE_STUDENT,
            "new_password": "Password123",
            "password_confirmation": "Password123",
        }
        self.student_user = User.objects.get(username="@johndoe")
