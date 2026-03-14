from django.core.validators import RegexValidator
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
    email = models.EmailField(unique=True, blank=False)
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default=USER_TYPE_STUDENT,
    )
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", null=True, blank=True
    )
    self_intro = models.TextField(blank=True, max_length=200)
    faculties = models.TextField(blank=True, help_text="Comma-separated faculty codes")
    study_levels = models.TextField(
        blank=True, help_text="Comma-separated study level codes"
    )
    categories = models.TextField(
        blank=True, help_text="Comma-separated category codes"
    )

    class Faculty(models.TextChoices):
        EMPTY = "", "Select"
        FOLSM = "folsm", "Faculty of Life Sciences & Medicine (FoLSM)"
        SSPP = "sspp", "Faculty of Social Science & Public Policy (SSPP)"
        NMPC = (
            "nmpc",
            "Florence Nightingale Faculty of Nursing, Midwifery & Palliative Care (NMPC)",
        )
        NMES = "nmes", "Faculty of Natural, Mathematical & Engineering Sciences (NMES)"
        AH = "ah", "Faculty of Arts & Humanities (A&H)"
        KBS = "kbs", "King's Business School (KBS)"
        DOCS = "docs", "Faculty of Dentistry, Oral & Craniofacial Sciences (DOCS)"
        DPSOL = "dpsol", "The Dickson Poon School of Law (DPSoL)"
        IOPPN = "ioppn", "Institute of Psychiatry, Psychology & Neuroscience (IoPPN)"

    class StudyLevel(models.TextChoices):
        EMPTY = "", "Select"
        UNDERGRADUATE = "undergraduate", "Undergraduate"
        POSTGRADUATE_TAUGHT = "postgraduate_taught", "Postgraduate Taught"
        POSTGRADUATE_RESEARCH = "postgraduate_research", "Postgraduate Research"
        OTHER = "other", "Other"

    preferred_name = models.CharField(max_length=100, blank=True)
    pronouns = models.CharField(max_length=50, blank=True)
    student_id = models.CharField(
        max_length=8,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\d{8}$", message="Student ID must be exactly 8 digits."
            )
        ],
    )
    phone_number = models.CharField(max_length=20, blank=True)
    faculty = models.CharField(max_length=100, blank=True, choices=Faculty.choices)
    study_level = models.CharField(
        max_length=100, blank=True, choices=StudyLevel.choices
    )
    graduation_year = models.PositiveIntegerField(null=True, blank=True)

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
