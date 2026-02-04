from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from tickets.models import Ticket
from tickets.models import User
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.paginator import Paginator


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
    tab = request.GET.get("tab", "open_tickets")
    TAB_LABELS = {
        "open_tickets": "Open",
        "in_progress_tickets": "In progress",
        "need_response_tickets": "Need response",
        "assigned_tickets": "Assigned",
        "overdue_tickets": "Overdue",
        "closed_tickets": "Closed",
    }

    if current_user.user_type == User.USER_TYPE_STAFF:
        tickets = Ticket.objects.all().order_by("-created_at")
        overdue_cutoff = timezone.now() - timedelta(days=5)

        groups = {
            "open_tickets": tickets.filter(
                assigned_to__isnull=True,
                status__in=[
                    Ticket.Status.AWAITING_STAFF,
                    Ticket.Status.AWAITING_STUDENT,
                ],
            ),
            "assigned_tickets": tickets.filter(assigned_to=current_user),
            "overdue_tickets": tickets.filter(created_at__lt=overdue_cutoff).exclude(
                status=Ticket.Status.CLOSED
            ),
            "closed_tickets": tickets.filter(status=Ticket.Status.CLOSED),
        }
    elif current_user.user_type == User.USER_TYPE_STUDENT:
        tickets = Ticket.objects.filter(student=current_user).order_by("-created_at")
        groups = {
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
        }

    if tab not in groups:
        tab = "open_tickets"

    qs = groups[tab]
    paginator = Paginator(qs, settings.ITEMS_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "dashboard.html",
        {
            "tickets": page_obj,
            "category": TAB_LABELS.get(tab, "N/A"),
            "page_obj": page_obj,
            "paginator": paginator,
            "tab": tab,
            "total": qs.count(),
        },
    )
