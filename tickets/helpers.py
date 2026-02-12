### Helper function and classes go here.

from django.conf import settings
from django.core.mail import send_mail


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
