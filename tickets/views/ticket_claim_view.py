from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views import View
from tickets.models import Ticket, User


@method_decorator(login_required, name="dispatch")
class TicketClaimView(View):

    @method_decorator(require_POST)
    def post(self, request, ticket_id):
        if request.user.user_type != User.USER_TYPE_STAFF:
            messages.error(request, "You are not a staff member!")
            return redirect("ticket_detail", pk=ticket_id)

        updated = Ticket.objects.filter(pk=ticket_id, assigned_to__isnull=True).update(
            assigned_to=request.user
        )

        if updated:
            messages.success(request, "You have claimed this ticket.")
            return redirect("ticket_detail", pk=ticket_id)

        ticket = get_object_or_404(
            Ticket.objects.select_related("assigned_to"), pk=ticket_id
        )

        if ticket.assigned_to == request.user:
            messages.success(request, "You have claimed this ticket.")
        else:
            messages.error(request, f"Ticket already claimed by {ticket.assigned_to}.")

        return redirect("ticket_detail", pk=ticket_id)
