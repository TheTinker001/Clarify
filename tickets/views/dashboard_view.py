from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from tickets.models import Ticket
from tickets.models import User
from django.utils import timezone
from datetime import timedelta


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
    context = {}

    if current_user.user_type == User.USER_TYPE_STAFF:
        tickets = Ticket.objects.all().order_by("-created_at")
        overdue_cutoff = timezone.now() - timedelta(days=5)

        context.update(
            {
                "open_tickets": tickets.filter(
                    assigned_to__isnull=True,
                    status__in=[
                        Ticket.Status.AWAITING_STAFF,
                        Ticket.Status.AWAITING_STUDENT,
                    ],
                ),
                "assigned_tickets": tickets.filter(assigned_to=current_user),
                "overdue_tickets": tickets.filter(
                    created_at__lt=overdue_cutoff
                ).exclude(status=Ticket.Status.CLOSED),
                "closed_tickets": tickets.filter(status=Ticket.Status.CLOSED),
                "role": "staff",
            }
        )
    elif current_user.user_type == User.USER_TYPE_STUDENT:
        tickets = Ticket.objects.filter(student=current_user).order_by("-created_at")
        context.update(
            {
                "open_tickets": tickets.filter(
                    assigned_to__isnull=True,
                ),
                "in_progress_tickets": tickets.filter(
                    assigned_to__isnull=False,
                ),
                "need_response_tickets": tickets.filter(
                    status=Ticket.Status.AWAITING_STUDENT
                ),
                "closed_tickets": tickets.filter(status=Ticket.Status.CLOSED),
                "role": "student",
            }
        )

    return render(request, "dashboard.html", context)
