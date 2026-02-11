from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views import View
from tickets.models import Ticket, User


@method_decorator([login_required, require_POST], name="dispatch")
class TicketClaimView(View):
    def post(self, request, url_code):
        ticket = get_object_or_404(
            Ticket.objects.select_related("assigned_to"),
            url_code=url_code,
        )

        if request.user.user_type != User.USER_TYPE_STAFF:
            messages.error(request, "You are not a staff member!")
            return redirect(ticket.get_absolute_url())

        updated = Ticket.objects.filter(
            url_code=url_code, assigned_to__isnull=True
        ).update(assigned_to=request.user)

        if updated:
            messages.success(request, "You have claimed this ticket.")
            return redirect(ticket.get_absolute_url())

        ticket.refresh_from_db(fields=["assigned_to"])
        if ticket.assigned_to_id == request.user.id:
            messages.success(request, "You have claimed this ticket.")
        else:
            messages.error(request, f"Ticket already claimed by {ticket.assigned_to}.")

        return redirect(ticket.get_absolute_url())
