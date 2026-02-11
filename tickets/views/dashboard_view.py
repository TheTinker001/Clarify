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
    Only logged-in users can access the page. If a user is not authenticated, they are automatically redirected to the login
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

        # staff cant see tickets assigned to others
        groups = {
            "open_tickets": tickets.filter(
                assigned_to__isnull=True,
                status__in=[
                    Ticket.Status.AWAITING_STAFF,
                    Ticket.Status.AWAITING_STUDENT,
                ],
                created_at__gte=overdue_cutoff,
            ),
            "assigned_tickets": tickets.filter(
                assigned_to=current_user,
                status__in=[
                    Ticket.Status.AWAITING_STAFF,
                    Ticket.Status.AWAITING_STUDENT,
                ],
            ),
            "overdue_tickets": tickets.filter(
                assigned_to__isnull=True,
                status=Ticket.Status.AWAITING_STAFF,
                created_at__lt=overdue_cutoff,
            ),
            "closed_tickets": tickets.filter(
                status=Ticket.Status.CLOSED,
            ),
        }
    elif current_user.user_type == User.USER_TYPE_STUDENT:
        tickets = Ticket.objects.filter(student=current_user).order_by("-created_at")
        groups = {
            "open_tickets": tickets.filter(
                status=Ticket.Status.AWAITING_STAFF,
                assigned_to__isnull=True,
            ),
            "in_progress_tickets": tickets.filter(
                status=Ticket.Status.AWAITING_STAFF,
                assigned_to__isnull=False,
            ),
            "need_response_tickets": tickets.filter(
                status=Ticket.Status.AWAITING_STUDENT,
            ),
            "closed_tickets": tickets.filter(
                status=Ticket.Status.CLOSED,
            ),
        }
    else:  # should never happen
        tickets = Ticket.objects.none()
        groups = {"open_tickets": tickets}

    if tab not in groups:
        tab = "open_tickets"

    if current_user.user_type == User.USER_TYPE_STAFF:
        sort = request.GET.get("sort", "")
        if sort == "high":
            qs = groups[tab].filter(priority=Ticket.Priority.HIGH)
        elif sort == "medium":
            qs = groups[tab].filter(priority=Ticket.Priority.MEDIUM)
        elif sort == "low":
            qs = groups[tab].filter(priority=Ticket.Priority.LOW)
        elif sort == "pending":
            qs = groups[tab].filter(priority=Ticket.Priority.PENDING_PRIORITY)
        else:
            qs = groups[tab]
        qs = qs.order_by("created_at")
    else:
        qs = groups[tab].order_by("created_at")

    paginator = Paginator(qs, settings.ITEMS_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()

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
            "querystring": querystring,
            "priority_sort": request.GET.get("sort", ""),
        },
    )
