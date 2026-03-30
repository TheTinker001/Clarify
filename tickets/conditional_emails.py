"""Conditional email helpers: reminders and ticket closure notifications."""

from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings


def _send_reminder_email(ticket):
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


def _send_ticket_closed_email(ticket, reason):
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


def send_reminder_emails(days=7):
    """Find tickets awaiting student for 7+ days and send reminders."""
    from tickets.models import Ticket

    cutoff = timezone.now() - timedelta(days=days)
    tickets = (
        Ticket.objects.filter(
            status=Ticket.Status.AWAITING_STUDENT,
            awaiting_student_since__isnull=False,
            awaiting_student_since__lte=cutoff,
            reminder_sent_at__isnull=True,
        )
        .exclude(status=Ticket.Status.CLOSED)
        .select_related("student")
    )

    count = 0
    for ticket in tickets:
        try:
            _send_reminder_email(ticket)
            ticket.reminder_sent_at = timezone.now()
            ticket.save(update_fields=["reminder_sent_at"])
            count += 1
        except Exception:
            pass
    return count


def close_inactive_tickets_with_email(days=14):
    """Close tickets inactive for 14+ days and email each student."""
    from tickets.models import Ticket

    cutoff = timezone.now() - timedelta(days=days)
    now = timezone.now()

    tickets = (
        Ticket.objects.filter(
            status=Ticket.Status.AWAITING_STUDENT,
            awaiting_student_since__isnull=False,
            awaiting_student_since__lte=cutoff,
        )
        .exclude(status=Ticket.Status.CLOSED)
        .select_related("student")
    )

    count = 0
    for ticket in tickets:
        ticket.status = Ticket.Status.CLOSED
        ticket.closed_reason = Ticket.ClosedReason.INACTIVITY
        ticket.closed_at = now
        ticket.awaiting_student_since = None
        ticket.reminder_sent_at = None
        ticket.save(
            update_fields=[
                "status",
                "closed_reason",
                "closed_at",
                "awaiting_student_since",
                "reminder_sent_at",
                "updated_at",
            ]
        )
        try:
            _send_ticket_closed_email(ticket, "inactivity")
        except Exception:
            pass
        count += 1
    return count
