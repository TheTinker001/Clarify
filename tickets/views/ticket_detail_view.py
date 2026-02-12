from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from tickets.forms.ticket_priority_form import TicketPriorityForm
from tickets.models import Ticket, User
from django.contrib import messages


@login_required
def ticket_detail(request, url_code):
    """Display a single ticket by primary key."""
    ticket = get_object_or_404(
        Ticket.objects.select_related("student", "assigned_to"),
        url_code=url_code,
    )

    is_staff_user = request.user.user_type == User.USER_TYPE_STAFF
    is_owner = ticket.student_id == request.user.id

    if request.method == "POST" and request.POST.get("action") == "set_priority":
        if request.user.user_type != User.USER_TYPE_STAFF:
            raise Http404

        if ticket.status == Ticket.Status.CLOSED:
            raise Http404

        form = TicketPriorityForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, "Priority updated.")
        else:
            messages.error(request, "Invalid priority.")
        return redirect("ticket_detail", url_code=url_code)

    if is_staff_user:
        priority_form = TicketPriorityForm(instance=ticket)
    else:
        priority_form = None

    if is_staff_user or is_owner:
        return render(
            request,
            "ticket_detail.html",
            {
                "ticket": ticket,
                "ticket_priority_form": priority_form,
            },
        )
    else:
        raise Http404
