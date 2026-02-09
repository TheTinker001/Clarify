from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from tickets.models import Ticket


@login_required
def ticket_detail(request, url_code):
    """Display a single ticket by primary key."""
    ticket = get_object_or_404(
        Ticket.objects.select_related("student", "assigned_to"),
        url_code=url_code,
    )
    return render(request, "ticket_detail.html", {"ticket": ticket})
