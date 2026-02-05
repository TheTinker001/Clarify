"""Unit tests of the user form."""

from django import forms
from django.test import TestCase
from tickets.forms import UserForm
from tickets.models import User


class UserFormTestCase(TestCase):
    """Unit tests of the user form."""

    fixtures = ["tickets/tests/fixtures/default_user.json"]

    def setUp(self):
        self.form_input = {
            "first_name": "Jimmy",
            "last_name": "Atom",
            "username": "@jimmyatom",
            "email": "jimmyatom@example.org",
        }

    def test_form_has_necessary_fields(self):
        form = UserForm()
        self.assertIn("first_name", form.fields)
        self.assertIn("last_name", form.fields)
        self.assertIn("username", form.fields)
        self.assertIn("email", form.fields)
        email_field = form.fields["email"]
        self.assertTrue(isinstance(email_field, forms.EmailField))

    def test_valid_user_form(self):
        form = UserForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_uses_model_validation(self):
        self.form_input["username"] = "badusername"
        form = UserForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_form_must_save_correctly(self):
        user = User.objects.get(username="@johndoe")
        form = UserForm(instance=user, data=self.form_input)
        before_count = User.objects.count()
        form.save()
        after_count = User.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(user.username, "@jimmyatom")
        self.assertEqual(user.first_name, "Jimmy")
        self.assertEqual(user.last_name, "Atom")
        self.assertEqual(user.email, "jimmyatom@example.org")
