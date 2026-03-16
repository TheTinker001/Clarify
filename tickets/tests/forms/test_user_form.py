"""Unit tests of the user form."""

from django import forms
from django.test import TestCase
from tickets.forms import UserForm, StaffPreferenceForm
from tickets.models import User
from tickets.models import Ticket
from django.core.files.uploadedfile import SimpleUploadedFile


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
        import sys

        print(form.errors, file=sys.stderr)
        print(form.errors)
        if not form.is_valid():
            raise Exception(form.errors)
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

    def test_user_form_profile_picture_and_self_intro(self):
        from PIL import Image
        import io

        user = User.objects.get(username="@johndoe")
        form_input = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
            "self_intro": "Updated intro",
        }
        image = Image.new("RGB", (10, 10), color="red")
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        pic = SimpleUploadedFile(
            "test.png", image_bytes.read(), content_type="image/png"
        )
        files = {"profile_picture": pic}
        form = UserForm(data=form_input, files=files, instance=user)
        if not form.is_valid():
            raise Exception(form.errors)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.self_intro, "Updated intro")
        self.assertTrue(user.profile_picture.name.startswith("profile_pictures/"))

    def test_clean_username_lowercases_input(self):
        user = User.objects.get(username="@johndoe")
        form = UserForm(
            instance=user, data={**self.form_input, "username": "@JIMMYATOM"}
        )
        form.is_valid()
        self.assertEqual(form.cleaned_data["username"], "@jimmyatom")

    def test_clean_username_with_none_does_not_crash(self):
        user = User.objects.get(username="@johndoe")
        form = UserForm(instance=user, data={**self.form_input, "username": ""})
        form.is_valid()
        self.assertIn("username", form.errors)


class StaffPreferenceFormTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="@staff",
            first_name="Staff",
            last_name="User",
            email="staff@example.com",
            user_type=User.USER_TYPE_STAFF,
        )
        self.form_data = {
            "faculties": [Ticket.Faculty.FOLSM, Ticket.Faculty.SSPP],
            "study_levels": [Ticket.StudyLevel.UNDERGRADUATE],
            "categories": [
                Ticket.Category.ASSESSMENT,
                Ticket.Category.HEALTH_AND_WELLBEING,
            ],
        }

    def get_form(self, instance=None, data=None):
        if data is None:
            data = self.form_data
        if instance is None:
            instance = self.user
        return StaffPreferenceForm(data=data, instance=instance)

    def test_valid_for_staff(self):
        form = self.get_form()
        self.assertTrue(form.is_valid())

    def test_saves_preferences(self):
        form = self.get_form()
        form.is_valid()
        user = form.save()
        self.assertEqual(
            user.faculties, f"{Ticket.Faculty.FOLSM},{Ticket.Faculty.SSPP}"
        )
        self.assertEqual(user.study_levels, Ticket.StudyLevel.UNDERGRADUATE)
        self.assertEqual(
            user.categories,
            f"{Ticket.Category.ASSESSMENT},{Ticket.Category.HEALTH_AND_WELLBEING}",
        )

    def test_only_staff_can_edit(self):
        form = self.get_form()
        self.assertTrue(form.is_valid())
        student = User.objects.create(
            username="@student",
            first_name="Student",
            last_name="User",
            email="student@example.com",
            user_type=User.USER_TYPE_STUDENT,
        )
        form = self.get_form(instance=student)
        self.assertFalse(form.is_valid())
        self.assertIn("Only staff can edit preferences.", str(form.errors))
