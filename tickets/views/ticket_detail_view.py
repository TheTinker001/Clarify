from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from tickets.forms.ticket_response_form import TicketResponseForm
from tickets.helpers import _send_staff_response_email
from tickets.models import Ticket, User


@login_required
def ticket_detail(request, url_code):
    """Display a single ticket and handle responses."""
    ticket = get_object_or_404(
        Ticket.objects.select_related("student", "assigned_to"),
        url_code=url_code,
    )

    is_staff_user = request.user.user_type == User.USER_TYPE_STAFF
    is_owner = ticket.student_id == request.user.id

    if not (is_staff_user or is_owner):
        raise Http404

    if request.method == "POST":
        form = TicketResponseForm(request.POST)
        if form.is_valid():
            response_obj = form.save(commit=False)
            response_obj.ticket = ticket
            response_obj.author = request.user

            if is_staff_user:
                ticket.status = Ticket.Status.AWAITING_STUDENT
                ticket.save()

                response_obj.save()

                try:
                    _send_staff_response_email(ticket, response_obj)
                except Exception:
                    pass

                messages.success(request, "Response sent.")
            else:
                ticket.status = Ticket.Status.AWAITING_STAFF
                ticket.save()

                response_obj.save()
                messages.success(request, "Response sent.")

            return redirect(ticket.get_absolute_url())
    else:
        form = TicketResponseForm()

    responses = ticket.responses.select_related("author").all()

    return render(
        request,
        "ticket_detail.html",
        {
            "ticket": ticket,
            "form": form,
            "responses": responses,
        },
    )
