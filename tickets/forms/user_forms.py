from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from tickets.models import User


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
        username = self.cleaned_data.get("username")
        if username:
            username = username.lower()
        return username


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

    class Meta:
        """Form options."""

        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "user_type",
        ]

    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        initial=User.USER_TYPE_STUDENT,
    )

    def save(self):
        """Create and return the new user via 'create_user' so the password is hashed correctly."""

        super().save(commit=False)
        user = User.objects.create_user(
            self.cleaned_data.get("username"),
            first_name=self.cleaned_data.get("first_name"),
            last_name=self.cleaned_data.get("last_name"),
            email=self.cleaned_data.get("email"),
            password=self.cleaned_data.get("new_password"),
            user_type=self.cleaned_data.get("user_type"),
        )
        return user

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username:
            username = username.lower()
        return username
