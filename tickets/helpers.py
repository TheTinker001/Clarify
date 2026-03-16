"""Shared file validation helpers, email utilities, and multi-file upload field for the tickets app."""

from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.mail import send_mail
from django.core.validators import FileExtensionValidator
from django import forms
from datetime import timedelta
from django.utils import timezone


def _validate_file_size(file):
    """Raise ValidationError if the uploaded file exceeds 5 MB."""
    max_size_mb = 5
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File size cannot exceed {max_size_mb}MB")


def _close_inactive_tickets(days=14):
    from tickets.models import Ticket

    cutoff = timezone.now() - timedelta(days=days)
    now = timezone.now()

    qs = Ticket.objects.filter(
        status=Ticket.Status.AWAITING_STUDENT,
        awaiting_student_since__isnull=False,
        awaiting_student_since__lte=cutoff,
    ).exclude(status=Ticket.Status.CLOSED)

    return qs.update(
        status=Ticket.Status.CLOSED,
        closed_reason=Ticket.ClosedReason.INACTIVITY,
        closed_at=now,
        awaiting_student_since=None,
    )


def _send_ticket_created_email(ticket):
    """Send confirmation email when a student creates a ticket."""
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return
    if not ticket.student.email:
        return

    subject_template = getattr(
        settings,
        "TICKET_CREATED_EMAIL_SUBJECT",
        "Confirmation of Ticket Submission - Reference #{ticket_id}",
    )
    body_template = getattr(
        settings,
        "TICKET_CREATED_EMAIL_BODY",
        (
            "Dear {first_name},\n\n"
            "Thank you for contacting the Clarify Support Team.\n\n"
            "We confirm that your enquiry has been successfully received and logged in our system. "
            "A member of our academic support staff will review your request and respond as soon as possible.\n\n"
            "Ticket Reference: {ticket_id}\n"
            "Subject: {subject}\n\n"
            "Please retain this reference number for future correspondence.\n\n"
            "Kind regards,\n"
            "Clarify Support Team"
        ),
    )
    subject = subject_template.format(
        ticket_id=ticket.pk,
        subject=ticket.subject,
        first_name=ticket.student.first_name or "student",
    )
    body = body_template.format(
        ticket_id=ticket.pk,
        subject=ticket.subject,
        first_name=ticket.student.first_name or "student",
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        recipient_list=[ticket.student.email],
        fail_silently=False,
    )


def _send_staff_comment_email(ticket, comment):
    """Send email to the student when staff comments on their ticket."""
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return
    if not ticket.student.email:
        return

    ticket_url = "{base}/ticket/{url_code}/".format(
        base=getattr(settings, "SITE_URL", "http://localhost:8000").rstrip("/"),
        url_code=ticket.url_code,
    )

    first_name = ticket.student.first_name or "student"
    subject = "Response to Your Support Ticket - {subject}".format(
        subject=ticket.subject
    )
    body = (
        "Dear {first_name},\n\n"
        "We are writing to inform you that a member of our academic staff has responded to your support request.\n\n"
        "Ticket Subject: {ticket_subject}\n\n"
        "Staff Response:\n"
        "{comment_body}\n\n"
        "You may review the full discussion and provide any further clarification using the link below:\n"
        "{ticket_url}\n\n"
        "If you require additional assistance, please do not hesitate to reply through the ticket system.\n\n"
        "Kind regards,\n"
        "Clarify Support Team"
    ).format(
        first_name=first_name,
        ticket_subject=ticket.subject,
        comment_body=comment.body,
        ticket_url=ticket_url,
    )

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        recipient_list=[ticket.student.email],
        fail_silently=False,
    )


def get_page_slots(cur, max_pages):
    if max_pages <= 9:
        return list(range(1, max_pages + 1))
    slots = []
    if cur <= 4:
        slots = list(range(1, 8)) + ["...", max_pages]
    elif cur >= max_pages - 3:
        slots = [1, "..."] + list(range(max_pages - 6, max_pages + 1))
    else:
        slots = [1, "..."] + list(range(cur - 2, cur + 3)) + ["...", max_pages]
    return slots


class MultipleFileInput(forms.ClearableFileInput):
    """File input widget that allows the user to select more than one file at a time."""

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Form field that validates and returns multiple uploaded files as a list."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        """
        Normalise data to a list and validate each file individually.

        Some parsers pass a bare file object instead of a one-element list when
        only one file is selected.
        Both cases are handled so callers always get a list.
        """
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = []
            for d in data:
                f = single_file_clean(d, initial)
                self._validate_single_file(f)
                result.append(f)
        else:
            result = [single_file_clean(data, initial)]
            self._validate_single_file(result[0])
        return result

    def _validate_single_file(self, f):
        """Run extension and size validators against a single file object."""
        if f:
            ext_validator = FileExtensionValidator(
                allowed_extensions=settings.ALLOWED_EXTENSIONS
            )
            ext_validator(f)
            _validate_file_size(f)
