from datetime import timedelta

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.generic import TemplateView

from tickets.models import Ticket, User

from django.db.models import Q, Value
from django.db.models.functions import Concat


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
            tickets = Ticket.objects.all()
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

        tab_qs = groups[tab]

        if current_user.user_type == User.USER_TYPE_STAFF:
            sort = self.request.GET.get("sort", "")
            if sort == "high":
                qs = tab_qs.filter(priority=Ticket.Priority.HIGH)
            elif sort == "medium":
                qs = tab_qs.filter(priority=Ticket.Priority.MEDIUM)
            elif sort == "low":
                qs = tab_qs.filter(priority=Ticket.Priority.LOW)
            elif sort == "pending":
                qs = tab_qs.filter(priority=Ticket.Priority.PENDING_PRIORITY)
            else:
                qs = tab_qs
            qs = qs.order_by(self.default_sorting)

            faculty_filter = self.request.GET.get("faculty", "")
            if faculty_filter:
                try:
                    qs = qs.filter(faculty=faculty_filter)
                except:
                    pass

            study_level_filter = self.request.GET.get("study_level", "")
            if study_level_filter:
                try:
                    qs = qs.filter(study_level=study_level_filter)
                except:
                    pass

            category_filter = self.request.GET.get("category", "")
            if category_filter:
                try:
                    qs = qs.filter(category=category_filter)
                except:
                    pass
        else:
            qs = tab_qs.order_by(self.default_sorting)

        return tab, qs

    def get_queryset_for_search_term(self, qs, current_user):
        # could use shlex in the future e.g., $username:"@johndoe"
        if current_user.user_type == User.USER_TYPE_STAFF:
            search_term = self.request.GET.get("searchTerm", "").strip()
            if search_term:
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

        tab, qs = self.get_queryset_for_tab(groups, tab, current_user)
        qs = self.get_queryset_for_search_term(qs, current_user)

        paginator = Paginator(qs, settings.ITEMS_PER_PAGE)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        params = self.request.GET.copy()
        params.pop("page", None)
        querystring = params.urlencode()

        context.update(
            {
                "tickets": page_obj,
                "category": self.TAB_LABELS.get(tab, "N/A"),
                "page_obj": page_obj,
                "paginator": paginator,
                "tab": tab,
                "total": qs.count(),
                "querystring": querystring,
                "priority_sort": self.request.GET.get("sort", ""),
                "searchTerm": self.get_search_term(),
                "faculty_choices": Ticket.Faculty.choices,
                "study_level_choices": Ticket.StudyLevel.choices,
                "category_choices": Ticket.Category.choices,
                "selected_faculty": self.request.GET.get("faculty", ""),
                "selected_study_level": self.request.GET.get("study_level", ""),
                "selected_category": self.request.GET.get("category", ""),
            }
        )
        return context
