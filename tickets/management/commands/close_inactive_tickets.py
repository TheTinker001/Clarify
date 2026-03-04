from datetime import timedelta
from django.utils import timezone
from tickets.models import Ticket


def close_inactive_tickets(days=14):
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
