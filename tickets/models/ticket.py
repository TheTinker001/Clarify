from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.validators import MaxLengthValidator
from django.utils import timezone
from django.urls import reverse
import secrets

User = get_user_model()


class Ticket(models.Model):
    """Model representing a student ticket."""

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

    class Category(models.TextChoices):
        EMPTY = "", "Select"
        ASSESSMENT = "assessment", "Assessment"
        WELFARE = "welfare", "Welfare"
        CAREERS = "careers", "Careers"
        FINANCIAL_ISSUES = "financial_issues", "Financial Issues"
        UNI_PROCEDURES_REGULATIONS = (
            "uni_procedures_regulations",
            "University Procedures & Regulations",
        )
        ADMINISTRATION = "administration", "Administration"
        APPEALS_COMPLAINTS_AND_MISCONDUCT = (
            "appeals_complaints_and_misconduct",
            "Appeals, Complaints & Misconduct",
        )
        DIGNITY_AND_INCLUSION = "dignity_and_inclusion", "Dignity & Inclusion"
        DISABILITY_SUPPORT = "disability_support", "Disability Support"
        DOCUMENT_AND_LETTER_REQUESTS = (
            "document_and_letter_requests",
            "Document & Letter Requests",
        )
        FEES_FUNDING_AND_MONEY_ADVICE = (
            "fees_funding_and_money_advice",
            "Fees, Funding & Money Advice",
        )
        GRADUATION = "graduation", "Graduation"
        HEALTH_AND_WELLBEING = "health_and_wellbeing", "Health & Wellbeing"
        HOUSING_AND_ACCOMMODATION_SUPPORT = (
            "housing_and_accommodation_support",
            "Housing & Accommodation Support",
        )
        INDUSTRIAL_ACTION = "industrial_action", "Industrial Action"
        NEW_STUDENTS = "new_students", "New Students"
        RETURNING_TO_STUDY = "returning_to_study", "Returning to Study"
        STUDENT_LIFE = "student_life", "Student Life"
        VISAS_IMMIGRATION_AND_SUPPORT = (
            "visas_immigration_and_support",
            "Visas, Immigration & Support",
        )
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        AWAITING_STAFF = "awaiting_staff", "Awaiting staff"
        AWAITING_STUDENT = "awaiting_student", "Awaiting student"
        CLOSED = "closed", "Closed"

    class ClosedReason(models.TextChoices):
        ANSWERED = "answered", "Answered"
        INACTIVITY = "inactivity", "Inactivity"

    class Priority(models.TextChoices):
        PENDING_PRIORITY = "pending priority", "Pending Priority"
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tickets",
        limit_choices_to={"user_type": User.USER_TYPE_STUDENT},
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        limit_choices_to={"user_type": User.USER_TYPE_STAFF},
    )

    faculty = models.CharField(
        max_length=100, choices=Faculty.choices, blank=False, null=False
    )
    study_level = models.CharField(
        max_length=100, choices=StudyLevel.choices, blank=False, null=False
    )
    category = models.CharField(
        max_length=100, choices=Category.choices, blank=False, null=False
    )

    subject = models.CharField(max_length=78)

    BODY_MAX_LENGTH = 50000
    body = models.TextField(
        max_length=BODY_MAX_LENGTH, validators=[MaxLengthValidator(BODY_MAX_LENGTH)]
    )

    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.AWAITING_STAFF
    )
    closed_reason = models.CharField(
        max_length=32, choices=ClosedReason.choices, null=True, blank=True
    )
    priority = models.CharField(
        max_length=32, choices=Priority.choices, default=Priority.PENDING_PRIORITY
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    url_code = models.CharField(max_length=64, unique=True, blank=True, null=False)

    def clean(self):
        super().clean()

        if self.student_id and self.student.user_type != User.USER_TYPE_STUDENT:
            raise ValidationError({"student": "Ticket can only be made by students."})

        if self.assigned_to and self.assigned_to.user_type != User.USER_TYPE_STAFF:
            raise ValidationError(
                {"assigned_to": "Tickets can only be assigned to staff."}
            )

        if self.status == self.Status.CLOSED:
            if self.closed_at is None:
                self.closed_at = timezone.now()
            if not self.closed_reason:
                raise ValidationError(
                    {"closed_reason": "Tickets need a reason for closing."}
                )
        else:
            self.closed_at = None
            self.closed_reason = None

    def save(self, *args, **kwargs):
        """
        Override save to ensure each ticket has a unique URL code.

        The URL code is generated using a cryptographically safe token and
        checked against the database to avoid collisions.
        """
        if not self.url_code:
            self.url_code = self.generate_unique_url_code()
        self.full_clean()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Return the absolute URL for this ticket's detail view.

        Returns:
            str: A fully resolved URL for this ticket's detail page.
        """
        return reverse("ticket_detail", kwargs={"url_code": self.url_code})

    def get_claim_url(self):
        """
        Return the absolute URL for this ticket's claim view.

        Returns:
            str: A fully resolved URL for this ticket's claim page.
        """
        return reverse("ticket_claim", kwargs={"url_code": self.url_code})

    def get_unclaim_url(self):
        """
        Return the absolute URL for this ticket's unclaim view.

        Returns:
            str: A fully resolved URL for this ticket's unclaim page.
        """
        return reverse("ticket_unclaim", kwargs={"url_code": self.url_code})

    def generate_unique_url_code(self):
        """
        Generate a unique URL-safe identifier for the ticket.

        Returns:
            str: A unique token usable as a ticket identifier.
        """
        code = secrets.token_urlsafe(7)
        while Ticket.objects.filter(url_code=code).exists():
            code = secrets.token_urlsafe(7)
        return code

    def __str__(self):
        """Return the ticket details for readable display."""
        return f"Ticket {self.pk} | {self.subject}"

    class Meta:
        """Model settings controlling ordering and behaviours."""

        ordering = ["-created_at"]
