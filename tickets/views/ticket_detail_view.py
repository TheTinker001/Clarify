from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from tickets.models import Ticket, User


@login_required
def ticket_detail(request, pk):
    """Display a single ticket by primary key."""
    ticket = get_object_or_404(
        Ticket.objects.select_related("student", "assigned_to"),
        pk=pk,
    )
    return render(request, "ticket_detail.html", {"ticket": ticket})


@require_POST
@login_required
def ticket_claim(request, ticket_id):
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


@require_POST
@login_required
def ticket_unclaim(request, ticket_id):
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
