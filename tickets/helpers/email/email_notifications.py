"""Email notifiction helper functions."""

from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.conf import settings


def send_ticket_created_email(ticket):
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


def send_staff_comment_email(ticket, comment):
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

    tagless_comment = strip_tags(comment.body).strip()

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
        comment_body=tagless_comment,
        ticket_url=ticket_url,
    )

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        recipient_list=[ticket.student.email],
        fail_silently=False,
    )


def send_reminder_email(ticket):
    """Send a 7-day reminder to a student who hasn't responded."""
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return
    if not ticket.student.email:
        return

    ticket_url = "{base}/ticket/{url_code}/".format(
        base=getattr(settings, "SITE_URL", "http://localhost:8000").rstrip("/"),
        url_code=ticket.url_code,
    )

    first_name = ticket.student.first_name or "student"
    subject = "Reminder: Your ticket is awaiting your response - {subj}".format(
        subj=ticket.subject,
    )
    body = (
        "Dear {first_name},\n\n"
        "This is a reminder that your support ticket is awaiting your response.\n\n"
        "Ticket Subject: {ticket_subject}\n\n"
        "If we do not hear from you within {reminder_days} days, your ticket will be "
        "automatically closed due to inactivity.\n\n"
        "Please respond here:\n{ticket_url}\n\n"
        "Kind regards,\n"
        "Clarify Support Team"
    ).format(
        first_name=first_name,
        ticket_subject=ticket.subject,
        ticket_url=ticket_url,
        reminder_days=settings.INACTIVE_TICKET_FIRST_REMINDER,
    )

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        recipient_list=[ticket.student.email],
        fail_silently=False,
    )


def send_ticket_closed_email(ticket, reason):
    """Send email notifying student their ticket was closed."""
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return
    if not ticket.student.email:
        return

    ticket_url = "{base}/ticket/{url_code}/".format(
        base=getattr(settings, "SITE_URL", "http://localhost:8000").rstrip("/"),
        url_code=ticket.url_code,
    )

    first_name = ticket.student.first_name or "student"
    subject = "Your ticket has been closed - {subj}".format(subj=ticket.subject)

    if reason == "inactivity":
        reason_text = (
            "Your ticket has been automatically closed due to inactivity. "
            "We did not receive a response within the required timeframe."
        )
    else:
        reason_text = "Your ticket has been closed as your query has been answered."

    body = (
        "Dear {first_name},\n\n"
        "{reason_text}\n\n"
        "Ticket Subject: {ticket_subject}\n\n"
        "If you believe this was closed in error or you need further assistance, "
        "you can reopen your ticket by responding here:\n{ticket_url}\n\n"
        "Kind regards,\n"
        "Clarify Support Team"
    ).format(
        first_name=first_name,
        reason_text=reason_text,
        ticket_subject=ticket.subject,
        ticket_url=ticket_url,
    )

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        recipient_list=[ticket.student.email],
        fail_silently=False,
    )


def send_missing_fields_reply(student_email, subject, missing_fields):
    """Send reply asking student to resend with missing fields."""
    fields_list = ", ".join(missing_fields)
    body = (
        "Dear Student,\n\n"
        "Thank you for your email. We were unable to automatically determine "
        "the following information from your message:\n\n"
        f"  Missing: {fields_list}\n\n"
        "Please reply to this email and include the following details so we "
        "can process your query:\n\n"
        "- Faculty (e.g. King's Business School, Engineering, Law, etc.)\n"
        "- Study Level (e.g. Undergraduate, Postgraduate Taught, PhD)\n"
        "- Category (e.g. Assessment, Health, Careers, Accommodation, etc.)\n\n"
        "Kind regards,\n"
        "Clarify Support Team"
    )
    send_mail(
        subject=f"Re: {subject} - Additional Information Required",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        recipient_list=[student_email],
        fail_silently=False,
    )
