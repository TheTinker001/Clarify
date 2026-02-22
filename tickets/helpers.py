### Helper function and classes go here.

from django.conf import settings
from django.core.mail import send_mail


def _send_ticket_created_email(ticket):
    """Send confirmation email when a student creates a ticket."""
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return
    if not ticket.student.email:
        return

    subject_template = getattr(
        settings,
        "TICKET_CREATED_EMAIL_SUBJECT",
        "Confirmation of Ticket Submission – Reference #{ticket_id}",
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


def _send_staff_response_email(ticket, response):
    """Send email to the student when staff responds to their ticket."""
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return
    if not ticket.student.email:
        return

    # TODO: Update SITE_URL in .env for production (localhost works as a fallback for now)
    ticket_url = "{base}/ticket/{url_code}/".format(
        base=getattr(settings, "SITE_URL", "http://localhost:8000").rstrip("/"),
        url_code=ticket.url_code,
    )

    first_name = ticket.student.first_name or "there"
    subject = "Response to Your Support Ticket – {subject}".format(
        subject=ticket.subject
    )
    body = (
        "Dear {first_name},\n\n"
        "We are writing to inform you that a member of our academic staff has responded to your support request.\n\n"
        "Ticket Subject: {ticket_subject}\n\n"
        "Staff Response:\n"
        "{response_body}\n\n"
        "You may review the full discussion and provide any further clarification using the link below:\n"
        "{ticket_url}\n\n"
        "If you require additional assistance, please do not hesitate to reply through the ticket system.\n\n"
        "Kind regards,\n"
        "Clarify Support Team"
    ).format(
        first_name=first_name,
        ticket_subject=ticket.subject,
        response_body=response.body,
        ticket_url=ticket_url,
    )

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        recipient_list=[ticket.student.email],
        fail_silently=False,
    )
