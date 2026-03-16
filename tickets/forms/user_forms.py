from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from tickets.models import User, Ticket


class UserForm(forms.ModelForm):
    """Form to update user profile information."""

    class Meta:
        """Form options."""

        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "profile_picture",
            "self_intro",
        ]
        widgets = {
            "self_intro": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Write your bio here..."}
            ),
        }

    def clean_username(self):
        return self.cleaned_data.get("username", "").lower()


class NewPasswordMixin(forms.Form):
    """Form mixin providing password and password confirmation fields with strength validation."""

    new_password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(),
        validators=[
            RegexValidator(
                regex=r"^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).*$",
                message=(
                    "Password must contain an uppercase character, "
                    "a lowercase character, and a number"
                ),
            )
        ],
    )
    password_confirmation = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput()
    )

    def clean(self):
        """Add an error to 'password_confirmation' if it does not match 'new_password'."""
        super().clean()
        new_password = self.cleaned_data.get("new_password")
        password_confirmation = self.cleaned_data.get("password_confirmation")
        if new_password != password_confirmation:
            self.add_error(
                "password_confirmation", "Confirmation does not match password."
            )
        return self.cleaned_data


class PasswordForm(NewPasswordMixin):
    """Form enabling authenticated users to change their password, verifying the current one first."""

    password = forms.CharField(label="Current password", widget=forms.PasswordInput())

    def __init__(self, user=None, **kwargs):
        """Store the current user instance for use in 'clean'."""

        super().__init__(**kwargs)
        self.user = user

    def clean(self):
        """Verify the current password is correct before accepting the new one."""

        super().clean()
        password = self.cleaned_data.get("password")
        if self.user is not None:
            user = authenticate(username=self.user.username, password=password)
        else:
            user = None
        if user is None:
            self.add_error("password", "Password is invalid")

    def save(self):
        """Set and save the new password on the user instance."""

        new_password = self.cleaned_data["new_password"]
        if self.user is not None:
            self.user.set_password(new_password)
            self.user.save()
        return self.user


class SignUpForm(NewPasswordMixin, forms.ModelForm):
    """Registration form that creates a new 'User' with a hashed password via 'create_user()'."""

    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        initial=User.USER_TYPE_STUDENT,
    )
    faculty = forms.ChoiceField(choices=Ticket.Faculty.choices, required=False)
    study_level = forms.ChoiceField(choices=Ticket.StudyLevel.choices, required=False)
    graduation_year = forms.IntegerField(required=False)

    class Meta:
        """Form options."""

        model = User
        fields = [
            "first_name",
            "last_name",
            "preferred_name",
            "pronouns",
            "username",
            "email",
            "user_type",
            "student_id",
            "phone_number",
            "faculty",
            "study_level",
            "graduation_year",
        ]

    def clean(self):
        """Require student-only fields for students and ignore them for staff accounts."""
        super().clean()
        cleaned_data = self.cleaned_data
        user_type = cleaned_data.get("user_type")

        if user_type == User.USER_TYPE_STUDENT:
            required_student_fields = {
                "student_id": "Student ID is required for student accounts.",
                "faculty": "Faculty is required for student accounts.",
                "study_level": "Study level is required for student accounts.",
                "graduation_year": "Graduation year is required for student accounts.",
            }
            for field_name, error_message in required_student_fields.items():
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, error_message)
        else:
            cleaned_data["student_id"] = ""
            cleaned_data["phone_number"] = ""
            cleaned_data["faculty"] = ""
            cleaned_data["study_level"] = ""
            cleaned_data["graduation_year"] = None

        return cleaned_data

    def save(self):
        """Create and return the new user via 'create_user' so the password is hashed correctly."""

        super().save(commit=False)
        user = User.objects.create_user(
            self.cleaned_data.get("username"),
            first_name=self.cleaned_data.get("first_name"),
            last_name=self.cleaned_data.get("last_name"),
            preferred_name=self.cleaned_data.get("preferred_name"),
            pronouns=self.cleaned_data.get("pronouns"),
            email=self.cleaned_data.get("email"),
            password=self.cleaned_data.get("new_password"),
            user_type=self.cleaned_data.get("user_type"),
            student_id=self.cleaned_data.get("student_id", ""),
            phone_number=self.cleaned_data.get("phone_number", ""),
            faculty=self.cleaned_data.get("faculty", ""),
            study_level=self.cleaned_data.get("study_level", ""),
            graduation_year=self.cleaned_data.get("graduation_year"),
        )
        return user

    def clean_username(self):
        return self.cleaned_data.get("username", "").lower()
