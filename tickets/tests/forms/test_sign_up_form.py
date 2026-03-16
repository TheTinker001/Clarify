"""Unit tests of the sign up form."""

from django.contrib.auth.hashers import check_password
from django import forms
from django.test import TestCase
from tickets.forms import SignUpForm
from tickets.models import Ticket, User


class SignUpFormTestCase(TestCase):
    """Unit tests of the sign up form."""

    def setUp(self):
        self.form_input = {
            "first_name": "Jane",
            "last_name": "Doe",
            "preferred_name": "Jane",
            "pronouns": "she/her",
            "username": "@janedoe",
            "email": "janedoe@example.org",
            "user_type": User.USER_TYPE_STUDENT,
            "student_id": "12345678",
            "phone_number": "+44 0000 000067",
            "faculty": Ticket.Faculty.FOLSM,
            "study_level": Ticket.StudyLevel.UNDERGRADUATE,
            "graduation_year": 2027,
            "new_password": "Password123",
            "password_confirmation": "Password123",
        }

    def test_valid_sign_up_form(self):
        form = SignUpForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_has_necessary_fields(self):
        form = SignUpForm()
        self.assertIn("first_name", form.fields)
        self.assertIn("last_name", form.fields)
        self.assertIn("preferred_name", form.fields)
        self.assertIn("pronouns", form.fields)
        self.assertIn("username", form.fields)
        self.assertIn("email", form.fields)
        email_field = form.fields["email"]
        self.assertTrue(isinstance(email_field, forms.EmailField))
        self.assertIn("user_type", form.fields)
        self.assertIn("student_id", form.fields)
        self.assertIn("phone_number", form.fields)
        self.assertIn("faculty", form.fields)
        self.assertIn("study_level", form.fields)
        self.assertIn("graduation_year", form.fields)
        self.assertIn("new_password", form.fields)
        new_password_widget = form.fields["new_password"].widget
        self.assertTrue(isinstance(new_password_widget, forms.PasswordInput))
        self.assertIn("password_confirmation", form.fields)
        password_confirmation_widget = form.fields["password_confirmation"].widget
        self.assertTrue(isinstance(password_confirmation_widget, forms.PasswordInput))

    def test_form_uses_model_validation(self):
        self.form_input["username"] = "badusername"
        form = SignUpForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_password_must_contain_uppercase_character(self):
        self.form_input["new_password"] = "password123"
        self.form_input["password_confirmation"] = "password123"
        form = SignUpForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_password_must_contain_lowercase_character(self):
        self.form_input["new_password"] = "PASSWORD123"
        self.form_input["password_confirmation"] = "PASSWORD123"
        form = SignUpForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_password_must_contain_number(self):
        self.form_input["new_password"] = "PasswordABC"
        self.form_input["password_confirmation"] = "PasswordABC"
        form = SignUpForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_new_password_and_password_confirmation_are_identical(self):
        self.form_input["password_confirmation"] = "WrongPassword123"
        form = SignUpForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_student_fields_are_required_for_student_accounts(self):
        self.form_input["student_id"] = ""
        self.form_input["faculty"] = ""
        self.form_input["study_level"] = ""
        self.form_input["graduation_year"] = ""
        form = SignUpForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertIn("student_id", form.errors)
        self.assertIn("faculty", form.errors)
        self.assertIn("study_level", form.errors)
        self.assertIn("graduation_year", form.errors)

    def test_staff_accounts_do_not_require_student_fields(self):
        self.form_input["user_type"] = User.USER_TYPE_STAFF
        self.form_input["student_id"] = ""
        self.form_input["phone_number"] = "+44 0000 000087"
        self.form_input["faculty"] = ""
        self.form_input["study_level"] = ""
        self.form_input["graduation_year"] = ""
        form = SignUpForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_must_save_correctly(self):
        form = SignUpForm(data=self.form_input)
        before_count = User.objects.count()
        self.assertTrue(form.is_valid())
        form.save()
        after_count = User.objects.count()
        self.assertEqual(after_count, before_count + 1)
        user = User.objects.get(username="@janedoe")
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.preferred_name, "Jane")
        self.assertEqual(user.pronouns, "she/her")
        self.assertEqual(user.email, "janedoe@example.org")
        self.assertEqual(user.user_type, User.USER_TYPE_STUDENT)
        self.assertEqual(user.student_id, "12345678")
        self.assertEqual(user.phone_number, "+44 0000 000067")
        self.assertEqual(user.faculty, Ticket.Faculty.FOLSM)
        self.assertEqual(user.study_level, Ticket.StudyLevel.UNDERGRADUATE)
        self.assertEqual(user.graduation_year, 2027)
        is_password_correct = check_password("Password123", user.password)
        self.assertTrue(is_password_correct)

    def test_save_clears_student_fields_for_staff_accounts(self):
        self.form_input["user_type"] = User.USER_TYPE_STAFF
        self.form_input["username"] = "@staffjane"
        self.form_input["email"] = "staffjane@example.org"
        form = SignUpForm(data=self.form_input)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.student_id, "")
        self.assertEqual(user.phone_number, "")
        self.assertEqual(user.faculty, "")
        self.assertEqual(user.study_level, "")
        self.assertIsNone(user.graduation_year)

    def test_clean_username_lowercases_input(self):
        self.form_input["username"] = "@JANEDOE"
        form = SignUpForm(data=self.form_input)
        form.is_valid()
        self.assertEqual(form.cleaned_data["username"], "@janedoe")
