from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from tickets.models import Ticket


@login_required
def dashboard(request):
    """
    Display the current user's dashboard.

    This view renders the dashboard page for the authenticated user.
    It ensures that only logged-in users can access the page. If a user
    is not authenticated, they are automatically redirected to the login
    page.
    """

    current_user = request.user
    user_tickets = Ticket.objects.filter(student=current_user)
    return render(
        request, "dashboard.html", {"user": current_user, "tickets": user_tickets}
    )
