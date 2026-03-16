from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar


class User(AbstractUser):
    """
    Custom user model for students and staff.

    Preference fields ('faculties', 'study_levels', 'categories') store
    comma-separated choice codes for simple filtering without extra joins.
    """

    class Meta:
        ordering = ["last_name", "first_name"]

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
    preferred_name = models.CharField(max_length=50, blank=False, default="")
    pronouns = models.CharField(max_length=50, blank=False, default="")
    email = models.EmailField(unique=True, blank=False)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default="",
        validators=[
            RegexValidator(
                regex=r"^[0-9+()\-\s]{7,20}$",
                message="Phone number may only contain digits, spaces, and +()- characters.",
            )
        ],
    )

    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default=USER_TYPE_STUDENT,
    )
    student_id = models.CharField(
        max_length=8,
        blank=True,
        default="",
        validators=[
            RegexValidator(
                regex=r"^\d{8}$",
                message="Student ID must be an 8 digit number.",
            )
        ],
    )

    faculty = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )
    study_level = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )
    graduation_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1900), MaxValueValidator(9999)],
    )
    self_intro = models.TextField(blank=True, max_length=200)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", null=True, blank=True
    )
    faculties = models.TextField(blank=True, help_text="Comma-separated faculty codes")
    study_levels = models.TextField(
        blank=True, help_text="Comma-separated study level codes"
    )
    categories = models.TextField(
        blank=True, help_text="Comma-separated category codes"
    )

    def full_name(self):
        """Return a string containing the user's full name."""

        return f"{self.first_name} {self.last_name}"

    def gravatar(self, size=120):
        """Return a Gravatar URL for the user's email, falling back to the 'mp' placeholder."""
        gravatar_object = Gravatar(self.email)
        gravatar_url = gravatar_object.get_image(size=size, default="mp")
        return gravatar_url

    def mini_gravatar(self):
        """Return a URL to a miniature version of the user's gravatar."""

        return self.gravatar(size=60)

    @property
    def get_initials(self):
        """Return the user's initials as a two-character uppercase string (e.g. 'JD')."""
        return self.first_name[0].upper() + self.last_name[0].upper()

    @property
    def faculty_label(self):
        """Return the faculty label for a student user."""
        from tickets.models.ticket import Ticket

        if self.faculty in Ticket.Faculty.values:
            return Ticket.Faculty(self.faculty).label
        return ""

    @property
    def study_level_label(self):
        """Return the study level label for a student user."""
        from tickets.models.ticket import Ticket

        if self.study_level in Ticket.StudyLevel.values:
            return Ticket.StudyLevel(self.study_level).label
        return ""
