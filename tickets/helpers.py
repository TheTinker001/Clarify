### Helper function and classes go here.
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.mail import send_mail
from django.core.validators import FileExtensionValidator
from django import forms


def _validate_file_size(file):
    max_size_mb = 5
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File size cannot exceed {max_size_mb}MB")


def _send_ticket_created_email(ticket):
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return
    if not ticket.student.email:
        return

    subject_template = getattr(
        settings, "TICKET_CREATED_EMAIL_SUBJECT", "We received your query"
    )
    body_template = getattr(
        settings,
        "TICKET_CREATED_EMAIL_BODY",
        (
            "Hi {first_name},\n\n"
            "Your ticket has been received. We'll review it and get back to you.\n\n"
            "Ticket ID: {ticket_id}\n"
            "Subject: {subject}\n\n"
            "Thanks,\n"
            "Clarify Team"
        ),
    )
    subject = subject_template.format(
        ticket_id=ticket.pk,
        subject=ticket.subject,
        first_name=ticket.student.first_name or "there",
    )
    body = body_template.format(
        ticket_id=ticket.pk,
        subject=ticket.subject,
        first_name=ticket.student.first_name or "there",
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        recipient_list=[ticket.student.email],
        fail_silently=False,
    )


ALLOWED_EXTENSIONS = ["pdf", "doc", "docx", "txt", "jpg", "jpeg", "png"]


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
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
        if f:
            ext_validator = FileExtensionValidator(
                allowed_extensions=ALLOWED_EXTENSIONS
            )
            ext_validator(f)
            _validate_file_size(f)
