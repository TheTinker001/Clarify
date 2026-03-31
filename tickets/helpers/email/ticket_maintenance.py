"""Ticket maintenance helper functions."""

from django.utils import timezone
from datetime import timedelta
from tickets.helpers.email.email_notifications import (
    send_reminder_email,
    send_ticket_closed_email,
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
            send_reminder_email(ticket)
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
            send_ticket_closed_email(ticket, "inactivity")
        except Exception:
            pass
        count += 1
    return count
