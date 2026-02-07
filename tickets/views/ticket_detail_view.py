from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from tickets.models import Ticket
from django.contrib import messages


@login_required
def ticket_detail(request, pk):
    """Display a single ticket by primary key."""
    ticket = get_object_or_404(
        Ticket.objects.select_related("student", "assigned_to"),
        pk=pk,
    )
    return render(request, "ticket_detail.html", {"ticket": ticket})


@login_required
def ticket_claim(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if request.user.user_type != "staff":
        messages.add_message(request, messages.ERROR, "You are not a staff member!")
        return render(request, "ticket_detail.html", {"ticket": ticket})
    if ticket.assigned_to and ticket.assigned_to != request.user:
        messages.add_message(
            request,
            messages.ERROR,
            f"Ticket already claimed by {ticket.assigned_to}.",
        )
        return render(request, "ticket_detail.html", {"ticket": ticket})
    ticket.assigned_to = request.user
    ticket.save()
    messages.add_message(request, messages.SUCCESS, "You have claimed this ticket.")
    return render(request, "ticket_detail.html", {"ticket": ticket})


@login_required
def ticket_unclaim(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    if request.user.user_type != "staff":
        messages.add_message(request, messages.ERROR, "You are not a staff member!")
        return render(request, "ticket_detail.html", {"ticket": ticket})
    if not ticket.assigned_to or ticket.assigned_to != request.user:
        messages.add_message(
            request, messages.ERROR, f"You are not assigned to this ticket."
        )
        return render(request, "ticket_detail.html", {"ticket": ticket})
    ticket.assigned_to = None
    ticket.save()
    messages.add_message(request, messages.SUCCESS, "You have unclaimed this ticket.")
    return render(request, "ticket_detail.html", {"ticket": ticket})
