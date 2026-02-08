from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views import View

from tickets.models import Ticket, User


@method_decorator(login_required, name="dispatch")
class TicketUnclaimView(View):
    @method_decorator(require_POST, name="dispatch")
    def post(self, request, ticket_id):
        if request.user.user_type != User.USER_TYPE_STAFF:
            messages.error(request, "You are not a staff member!")
            return redirect("ticket_detail", pk=ticket_id)

        updated = Ticket.objects.filter(pk=ticket_id, assigned_to=request.user).update(
            assigned_to=None
        )

        if updated == 0:
            messages.error(request, "You are not assigned to this ticket.")
        else:
            messages.success(request, "You have unclaimed this ticket.")

        return redirect("ticket_detail", pk=ticket_id)
