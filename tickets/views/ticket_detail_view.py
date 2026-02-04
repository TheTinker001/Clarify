from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from tickets.models import Ticket


@login_required
def ticket_detail(request, pk):
    """Display a single ticket by primary key."""
    ticket = get_object_or_404(
        Ticket.objects.select_related('created_by', 'assigned_to'),
        pk=pk,
    )
    return render(request, 'ticket_detail.html', {'ticket': ticket})
