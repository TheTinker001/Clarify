from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views import View
from tickets.models import Ticket, User
from django.db import transaction


@method_decorator([login_required, require_POST], name="dispatch")
class TicketClaimView(View):
    """
    Let staff assign themselves to an unassigned ticket.

    Uses a filtered '.update(assigned_to__isnull=True)' to avoid race conditions.
    If zero rows are updated, the DB is re-read to determine who claimed it first.
    """

    def post(self, request, url_code):
        """Process the claim request and redirect back to the ticket detail page."""
        ticket = get_object_or_404(Ticket, url_code=url_code)

        if request.user.user_type != User.USER_TYPE_STAFF:
            messages.error(request, "You are not a staff member!")
            return redirect(ticket.get_absolute_url())

        with transaction.atomic():
            ticket = get_object_or_404(
                Ticket.objects.select_for_update(),
                url_code=url_code,
            )

            if ticket.assigned_to.filter(id=request.user.id).exists():
                messages.success(request, "You have already claimed this ticket.")
                return redirect(ticket.get_absolute_url())

            if ticket.assigned_to.count() >= 5:
                assigned_users = ", ".join(
                    str(user) for user in ticket.assigned_to.all()
                )
                messages.error(
                    request,
                    f"Ticket already has the maximum number of staff assigned: {assigned_users}.",
                )
                return redirect(ticket.get_absolute_url())

            ticket.assigned_to.add(request.user)
            messages.success(request, "You have claimed this ticket.")

        return redirect(ticket.get_absolute_url())
