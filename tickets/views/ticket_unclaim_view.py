from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from tickets.models import Ticket, User


@method_decorator([login_required, require_POST], name="dispatch")
class TicketUnclaimView(View):
    """Let staff remove their assignment. A filtered update ensures they can't unclaim another staff member's ticket."""

    def post(self, request, url_code):
        """Process the unclaim request and redirect back to the ticket detail page."""
        ticket = get_object_or_404(Ticket, url_code=url_code)

        if request.user.user_type != User.USER_TYPE_STAFF:
            messages.error(request, "You are not a staff member!")
            return redirect(ticket.get_absolute_url())

        if ticket.assigned_to.filter(id=request.user.id).exists():
            ticket.assigned_to.remove(request.user)
            messages.success(request, "You have unclaimed this ticket.")
        else:
            messages.error(request, "You are not assigned to this ticket.")

        return redirect(ticket.get_absolute_url())
