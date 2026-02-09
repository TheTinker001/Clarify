from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from tickets.models import Ticket, User


@login_required
def ticket_detail(request, url_code):
    """Display a single ticket by primary key."""
    ticket = get_object_or_404(
        Ticket.objects.select_related("student", "assigned_to"),
        url_code=url_code,
    )

    is_staff_user = request.user.user_type == User.USER_TYPE_STAFF
    is_owner = ticket.student_id == request.user.id

    if is_staff_user or is_owner:
        return render(request, "ticket_detail.html", {"ticket": ticket})
    else:
        raise Http404
