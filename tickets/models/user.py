from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar


class User(AbstractUser):
    """Model used for user authentication, and team member related information."""

    USER_TYPE_STUDENT = "student"
    USER_TYPE_STAFF = "staff"
    USER_TYPE_CHOICES = [
        (USER_TYPE_STUDENT, "Student"),
        (USER_TYPE_STAFF, "Staff"),
    ]

    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^@\w{3,}$",
                message="Username must consist of @ followed by at least three alphanumericals",
            )
        ],
    )
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(unique=True, blank=False)
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default=USER_TYPE_STUDENT,
    )
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", null=True, blank=True
    )
    self_intro = models.TextField(
        default="Hello! My friends!", blank=True, max_length=200
    )
    faculties = models.TextField(blank=True, help_text="Comma-separated faculty codes")
    study_levels = models.TextField(
        blank=True, help_text="Comma-separated study level codes"
    )
    categories = models.TextField(
        blank=True, help_text="Comma-separated category codes"
    )

    class Meta:
        """Model options."""

        ordering = ["last_name", "first_name"]

    def full_name(self):
        """Return a string containing the user's full name."""

        return f"{self.first_name} {self.last_name}"

    def gravatar(self, size=120):
        """Return a URL to the user's gravatar."""

        gravatar_object = Gravatar(self.email)
        gravatar_url = gravatar_object.get_image(size=size, default="mp")
        return gravatar_url

    def mini_gravatar(self):
        """Return a URL to a miniature version of the user's gravatar."""

        return self.gravatar(size=60)

    @property
    def get_initials(self):
        return self.first_name[0].upper() + self.last_name[0].upper()
