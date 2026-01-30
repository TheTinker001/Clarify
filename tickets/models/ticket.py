from django.db import models
from django.core.validators import MaxLengthValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class Ticket(models.Model):
    """Model representing a student ticket."""

    FACULTIES = [
        "Faculty of Life Sciences & Medicine (FoLSM)",
        "Faculty of Social Science & Public Policy (SSPP)",
        "Florence Nightingale Faculty of Nursing, Midwifery & Palliative Care (NMPC)",
        "Faculty of Natural, Mathematical & Engineering Sciences (NMES)",
        "Faculty of Arts & Humanities (A&H)",
        "King's Business School (KBS)",
        "Faculty of Dentistry, Oral & Craniofacial Sciences (DOCS)",
        "The Dickson Poon School of Law (DPSoL)",
        "Institute of Psychiatry, Psychology & Neuroscience (IoPPN)",
    ]

    STUDY_LEVEL = ["Undergraduate", "Postgraduate Taught", "Postgraduate"]

    CATEGORIES = [
        "Assessment",
        "Welfare",
        "Health",
        "Careers",
        "Financial Issues",
        "University Procedures and Regulations",
        "Misconduct Allegations",
        "Other",
    ]

    STATUS = ["Awaiting staff", "Awaiting student", "Closed"]
    CLOSED_REASONS = ["None", "Answered", "Inactivity"]

    """
    student = models.ForeignKey(
        User.USER_TYPE_STUDENT, on_delete=models.CASCADE, related_name="tickets"
    )
    """
    faculty = models.CharField(
        max_length=100, choices=[(fac, fac) for fac in FACULTIES]
    )
    study_level = models.CharField(
        max_length=100, choices=[(level, level) for level in STUDY_LEVEL]
    )
    category = models.CharField(
        max_length=100, choices=[(cat, cat) for cat in CATEGORIES]
    )
    subject = models.CharField(max_length=78)
    body = models.TextField(validators=[MaxLengthValidator(50000)])

    status = models.CharField(
        max_length=100, choices=[(stat, stat) for stat in STATUS], default=STATUS[0]
    )
    closed_reason = models.CharField(
        max_length=100,
        choices=[(reason, reason) for reason in CLOSED_REASONS],
        default=CLOSED_REASONS[0],
    )


"""
TODO

- wait for Gor code
- test Gor code in browser
- see if what I have for student works by creating tickets in the shell
- add tests similar to user tests

"""
