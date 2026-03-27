from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.generic import TemplateView
from tickets.helpers import get_page_slots
from django.db.models import Q, Value, Count
from django.db.models.functions import Concat
from tickets.models import Ticket, User
from datetime import timedelta
from clarify.settings import ITEMS_PER_PAGE, MAX_TICKET_CLAIMANTS


class DashboardView(LoginRequiredMixin, TemplateView):
    """Render the authenticated user's dashboard with tab-filtered, searchable, paginated tickets."""

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
    default_pk = "-pk"

    def get_tab(self):
        """Return the active tab key from the query string, falling back to 'open_tickets'."""
        tab = self.request.GET.get("tab", "open_tickets")
        if tab not in self.TAB_LABELS:
            tab = "open_tickets"
        return tab

    def get_QS_by_user_type(self, current_user):
        """
        Return per-tab querysets filtered by the user's role.

        Staff tabs: 'open_tickets' (unassigned <= 5 days), 'assigned_tickets',
        'overdue_tickets' (unassigned > 5 days), 'closed_tickets'.

        Student tabs: 'open_tickets' (unassigned), 'in_progress_tickets' (assigned),
        'need_response_tickets' (AWAITING_STUDENT), 'closed_tickets'.
        """
        if current_user.user_type == User.USER_TYPE_STAFF:

            def split_codes(s):
                return [c.strip() for c in s.split(",") if c.strip()]

            faculties = split_codes(current_user.faculties)
            study_levels = split_codes(current_user.study_levels)
            categories = split_codes(current_user.categories)

            delay_minutes = getattr(
                settings, "TICKET_STAFF_VISIBILITY_DELAY_MINUTES", 15
            )

            tickets = Ticket.objects.filter(
                Q(faculty__in=faculties)
                & Q(study_level__in=study_levels)
                & Q(category__in=categories)
            )

            if delay_minutes > 0:
                visibility_cutoff = timezone.now() - timedelta(minutes=delay_minutes)
                tickets = tickets.filter(created_at__lte=visibility_cutoff)

            overdue_cutoff = timezone.now() - timedelta(days=5)

            groups = {
                "open_tickets": tickets.annotate(
                    assigned_count=Count("assigned_to", distinct=True)
                ).filter(
                    assigned_count__lt=MAX_TICKET_CLAIMANTS,
                    status__in=[
                        Ticket.Status.AWAITING_STAFF,
                        Ticket.Status.AWAITING_STUDENT,
                    ],
                    created_at__gte=overdue_cutoff,
                ),
                "assigned_tickets": Ticket.objects.filter(
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
                ).distinct(),
                "need_response_tickets": tickets.filter(
                    status=Ticket.Status.AWAITING_STUDENT,
                ),
                "closed_tickets": tickets.filter(
                    status=Ticket.Status.CLOSED,
                ),
            }
        else:
            # Guard against future user types or data corruption.
            # Returns an empty queryset.
            tickets = Ticket.objects.none()
            groups = {"open_tickets": tickets}

        return groups

    def get_queryset_for_tab_by_filters(self, groups, tab, current_user):
        """Apply staff-only URL filter paramaters (priority, faculty, study_level, category) to the active tab's queryset."""
        if tab not in groups:
            tab = "open_tickets"

        qs = groups[tab]

        if current_user.user_type == User.USER_TYPE_STAFF:
            priority_filter = self.request.GET.get("priority", "")
            if priority_filter and priority_filter in dict(Ticket.Priority.choices):
                qs = qs.filter(priority=priority_filter)

            faculty_filter = self.request.GET.get("faculty", "")
            if faculty_filter and faculty_filter in dict(Ticket.Faculty.choices):
                qs = qs.filter(faculty=faculty_filter)

            study_level_filter = self.request.GET.get("study_level", "")
            if study_level_filter and study_level_filter in dict(
                Ticket.StudyLevel.choices
            ):
                qs = qs.filter(study_level=study_level_filter)

            category_filter = self.request.GET.get("category", "")
            if category_filter and category_filter in dict(Ticket.Category.choices):
                qs = qs.filter(category=category_filter)

        if current_user.user_type == User.USER_TYPE_STAFF:
            order_filter = self.request.GET.get("order", "newest")
            if order_filter == "oldest":
                qs = qs.order_by("created_at", "pk")
            else:
                qs = qs.order_by(self.default_sorting, self.default_pk)
        else:
            qs = qs.order_by(self.default_sorting, self.default_pk)

        return tab, qs

    def get_queryset_for_search_term(self, qs, current_user, search_term):
        """Filter the queryset by search term across subject, body, student username, and full name (staff only)."""
        if current_user.user_type == User.USER_TYPE_STAFF and search_term:
            order_filter = self.request.GET.get("order", "newest")

            if order_filter == "oldest":
                ordering = ("created_at", "pk")
            else:
                ordering = (self.default_sorting, self.default_pk)

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
                .order_by(*ordering)
            )
        return qs

    def get_search_term(self):
        """
        Return the search term, persisting it in the session across tab changes.

        If 'searchTerm' is in the query string, save it.
        If only 'tab' is present, return the session-stored value.
        Otherwise clear the session key and return ''.
        """
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
        """
        Build the dashboard template context.

        'querystring' preserves filters for pagination.
        'carry_querystring' omits 'tab' so tab links can append their own value while keeping filters intact.
        """
        context = super().get_context_data(**kwargs)

        current_user = self.request.user
        groups = self.get_QS_by_user_type(current_user)
        tab = self.get_tab()

        search_term = self.get_search_term()

        tab, qs = self.get_queryset_for_tab_by_filters(groups, tab, current_user)
        qs = self.get_queryset_for_search_term(qs, current_user, search_term)

        paginator = Paginator(qs, ITEMS_PER_PAGE)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        cur = page_obj.number
        max_pages = paginator.num_pages
        page_slots = get_page_slots(cur, max_pages)

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
                "max_pages": max_pages,
                "cur": cur,
                "page_slots": page_slots,
                "tab": tab,
                "total": qs.count(),
                "querystring": querystring,
                "carry_querystring": carry_querystring,
                "searchTerm": search_term,
                "filters": {
                    "priority": self.request.GET.get("priority", ""),
                    "faculty": self.request.GET.get("faculty", ""),
                    "study_level": self.request.GET.get("study_level", ""),
                    "category": self.request.GET.get("category", ""),
                    "order": self.request.GET.get("order", "newest"),
                },
                "filter_choices": {
                    "priority": Ticket.Priority.choices,
                    "faculty": Ticket.Faculty.choices,
                    "study_level": Ticket.StudyLevel.choices,
                    "category": Ticket.Category.choices,
                },
            }
        )
        return context
