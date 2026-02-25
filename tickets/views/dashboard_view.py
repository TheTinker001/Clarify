from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.generic import TemplateView
from django.db.models import Q, Value
from tickets.models import Ticket, User

from django.db.models.functions import Concat

from datetime import timedelta


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Display the current user's dashboard.

    This view renders the dashboard page for the authenticated user.
    Only logged-in users can access the page.
    If a user is not authenticated, they are automatically redirected to the login page.
    """

    template_name = "dashboard.html"
    TAB_LABELS = {
        "open_tickets": "Open",
        "in_progress_tickets": "In progress",
        "need_response_tickets": "Need response",
        "assigned_tickets": "Assigned",
        "overdue_tickets": "Overdue",
        "closed_tickets": "Closed",
    }
    default_sorting = "-created_at"

    def get_tab(self):
        tab = self.request.GET.get("tab", "open_tickets")
        if tab not in self.TAB_LABELS:
            tab = "open_tickets"
        return tab

    def get_QS_by_user_type(self, current_user):
        if current_user.user_type == User.USER_TYPE_STAFF:

            def split_codes(s):
                return [c.strip() for c in s.split(",") if c.strip()]

            faculties = split_codes(current_user.faculties)
            study_levels = split_codes(current_user.study_levels)
            categories = split_codes(current_user.categories)

            tickets = (
                Ticket.objects.all()
                .order_by("-created_at")
                .filter(
                    Q(faculty__in=faculties)
                    & Q(study_level__in=study_levels)
                    & Q(category__in=categories)
                )
                .distinct()
            )
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
            tickets = Ticket.objects.filter(student=current_user)
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
        return groups

    def get_queryset_for_tab(self, groups, tab, current_user):
        if tab not in groups:
            tab = "open_tickets"

        if current_user.user_type == User.USER_TYPE_STAFF:
            sort = self.request.GET.get("sort", "")
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
            qs = qs.order_by(self.default_sorting)
        else:
            qs = groups[tab].order_by(self.default_sorting)

        return tab, qs

    def get_queryset_for_search_term(self, qs, current_user, search_term):
        if current_user.user_type == User.USER_TYPE_STAFF and search_term:
            qs = (
                qs.annotate(
                    student_full_name=Concat(
                        "student__first_name", Value(" "), "student__last_name"
                    )
                )
                .filter(
                    Q(subject__icontains=search_term)
                    | Q(body__icontains=search_term)
                    | Q(student__username__icontains=search_term)
                    | Q(student_full_name__icontains=search_term)
                )
                .order_by(self.default_sorting)
            )
        return qs

    # Search term is stored in the session to preserve between tab changes to make it easier to search without retyping between tab changes.
    # Ideally cleared when user goes to a different page other than dashboard, detected with missing tab parameter
    def get_search_term(self):
        term = self.request.GET.get("searchTerm", None)

        if term is not None:
            term = term.strip()
            self.request.session["dashboard_searchTerm"] = term
            return term

        if "tab" in self.request.GET:
            return self.request.session.get("dashboard_searchTerm", "")

        self.request.session.pop("dashboard_searchTerm", None)
        return ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_user = self.request.user
        groups = self.get_QS_by_user_type(current_user)
        tab = self.get_tab()

        # Get session-backed search term once
        search_term = self.get_search_term()

        tab, qs = self.get_queryset_for_tab(groups, tab, current_user)
        qs = self.get_queryset_for_search_term(qs, current_user, search_term)

        paginator = Paginator(qs, settings.ITEMS_PER_PAGE)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        params = self.request.GET.copy()
        params.pop("page", None)

        # Ensure searchTerm is present in the URL if session has it
        if search_term:
            params["searchTerm"] = search_term
        else:
            params.pop("searchTerm", None)

        querystring = params.urlencode()

        # For tab links: keep everything except tab + page
        carry_params = params.copy()
        carry_params.pop("tab", None)
        carry_querystring = carry_params.urlencode()

        context.update(
            {
                "tickets": page_obj,
                "category": self.TAB_LABELS.get(tab, "N/A"),
                "page_obj": page_obj,
                "paginator": paginator,
                "tab": tab,
                "total": qs.count(),
                "querystring": querystring,
                "carry_querystring": carry_querystring,
                "priority_sort": self.request.GET.get("sort", ""),
                "searchTerm": search_term,
            }
        )
        return context
