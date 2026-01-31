from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.validators import MaxLengthValidator
from django.utils import timezone

User = get_user_model()


class Ticket(models.Model):
    """Model representing a student ticket."""

    class Faculty(models.TextChoices):
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
        UNDERGRADUATE = "undergraduate", "Undergraduate"
        POSTGRADUATE_TAUGHT = "postgraduate_taught", "Postgraduate Taught"
        POSTGRADUATE = "postgraduate", "Postgraduate"

    class Category(models.TextChoices):
        ASSESSMENT = "assessment", "Assessment"
        WELFARE = "welfare", "Welfare"
        HEALTH = "health", "Health"
        CAREERS = "careers", "Careers"
        FINANCIAL_ISSUES = "financial_issues", "Financial Issues"
        UNI_PROCEDURES_REGULATIONS = (
            "uni_procedures_regulations",
            "University Procedures and Regulations",
        )
        MISCONDUCT_ALLEGATIONS = "misconduct_allegations", "Misconduct Allegations"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        AWAITING_STAFF = "awaiting_staff", "Awaiting staff"
        AWAITING_STUDENT = "awaiting_student", "Awaiting student"
        CLOSED = "closed", "Closed"

    class ClosedReason(models.TextChoices):
        ANSWERED = "answered", "Answered"
        INACTIVITY = "inactivity", "Inactivity"

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

    faculty = models.CharField(max_length=64, choices=Faculty.choices)
    study_level = models.CharField(max_length=64, choices=StudyLevel.choices)
    category = models.CharField(max_length=64, choices=Category.choices)

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
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()

        if self.student and self.student.user_type != User.USER_TYPE_STUDENT:
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
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Ticket {self.pk} | {self.subject}"

    class Meta:
        ordering = ["-created_at"]
