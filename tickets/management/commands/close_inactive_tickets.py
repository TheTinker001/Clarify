from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from tickets.models import Ticket


class Command(BaseCommand):
    """
    Close tickets in AWAITING_STUDENT for more than 14 days (run on a schedule).

    The ``.exclude(status=CLOSED)`` guard is redundant but prevents accidental
    re-closure if data is ever in an inconsistent state.
    """

    help = (
        "Close tickets that have been awaiting student response for more than 14 days."
    )

    def handle(self, *args, **options):
        """Bulk-update all tickets past the inactivity threshold to CLOSED/INACTIVITY."""
        cutoff = timezone.now() - timedelta(days=14)

        qs = Ticket.objects.filter(
            status=Ticket.Status.AWAITING_STUDENT,
            awaiting_student_since__isnull=False,
            awaiting_student_since__lte=cutoff,
        ).exclude(status=Ticket.Status.CLOSED)

        now = timezone.now()
        updated = qs.update(
            status=Ticket.Status.CLOSED,
            closed_reason=Ticket.ClosedReason.INACTIVITY,
            closed_at=now,
        )

        self.stdout.write(self.style.SUCCESS(f"Closed {updated} inactive tickets."))
