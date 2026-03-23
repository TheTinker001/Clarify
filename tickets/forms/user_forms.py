from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from tickets.models import User, Ticket


class UserForm(forms.ModelForm):
    """Form to update user profile information."""

    preferred_name = forms.CharField(required=False)
    pronouns = forms.CharField(required=False)

    class Meta:
        """Form options."""

        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "preferred_name",
            "pronouns",
            "email",
            "phone_number",
            "self_intro",
            "profile_picture",
        ]
        widgets = {
            "self_intro": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Write your bio here..."}
            ),
        }

    def clean_username(self):
        return self.cleaned_data.get("username", "").lower()

    def clean_preferred_name(self):
        value = self.cleaned_data.get("preferred_name")
        return value or self.instance.preferred_name

    def clean_pronouns(self):
        value = self.cleaned_data.get("pronouns")
        return value or self.instance.pronouns


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

    preferred_name = forms.CharField(required=False)
    pronouns = forms.CharField(required=False)

    student_id = forms.CharField(
        required=False,
        validators=[
            RegexValidator(
                regex=r"^\d{8}$",
                message="Student ID must be an 8 digit number.",
            )
        ],
    )
    phone_number = forms.CharField(required=False)
    faculty = forms.ChoiceField(
        required=False,
        choices=Ticket.Faculty.choices,
    )
    study_level = forms.ChoiceField(
        required=False,
        choices=Ticket.StudyLevel.choices,
    )
    graduation_year = forms.IntegerField(required=False)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "preferred_name",
            "pronouns",
            "email",
            "phone_number",
            "user_type",
            "student_id",
            "faculty",
            "study_level",
            "graduation_year",
        ]

    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        initial=User.USER_TYPE_STUDENT,
    )

    def clean_username(self):
        return self.cleaned_data.get("username", "").lower()

    def clean(self):
        super().clean()

        user_type = self.cleaned_data.get("user_type")

        if user_type == User.USER_TYPE_STUDENT:
            required_student_fields = {
                "student_id": "Student ID is required for students.",
                "faculty": "Faculty is required for students.",
                "study_level": "Study level is required for students.",
                "graduation_year": "Graduation year is required for students.",
            }

            for field, message in required_student_fields.items():
                if not self.cleaned_data.get(field):
                    self.add_error(field, message)

        return self.cleaned_data

    def save(self):
        user_type = self.cleaned_data.get("user_type")

        if user_type == User.USER_TYPE_STUDENT:
            phone_number = self.cleaned_data.get("phone_number", "")
        else:
            phone_number = ""

        if user_type == User.USER_TYPE_STUDENT:
            student_id = self.cleaned_data.get("student_id", "")
        else:
            student_id = ""

        if user_type == User.USER_TYPE_STUDENT:
            faculty = self.cleaned_data.get("faculty", "")
        else:
            faculty = ""

        if user_type == User.USER_TYPE_STUDENT:
            study_level = self.cleaned_data.get("study_level", "")
        else:
            study_level = ""

        if user_type == User.USER_TYPE_STUDENT:
            graduation_year = self.cleaned_data.get("graduation_year")
        else:
            graduation_year = None

        user = User.objects.create_user(
            self.cleaned_data.get("username"),
            first_name=self.cleaned_data.get("first_name"),
            last_name=self.cleaned_data.get("last_name"),
            email=self.cleaned_data.get("email"),
            password=self.cleaned_data.get("new_password"),
            user_type=user_type,
            preferred_name=self.cleaned_data.get("preferred_name", ""),
            pronouns=self.cleaned_data.get("pronouns", ""),
            phone_number=phone_number,
            student_id=student_id,
            faculty=faculty,
            study_level=study_level,
            graduation_year=graduation_year,
        )
        return user
