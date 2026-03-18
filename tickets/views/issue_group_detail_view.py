from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from tickets.models import User, IssueGroup, Ticket
from django.core.paginator import Paginator

from clarify.settings import ITEMS_PER_PAGE


class IssueGroupDetailView(LoginRequiredMixin, TemplateView):
    """Display a specific issue group to staff users."""

    template_name = "issue_group_detail.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type != User.USER_TYPE_STAFF:
            return redirect("dashboard")

        self.issue_group = get_object_or_404(IssueGroup, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["issue_group"] = self.issue_group
        qs = self.get_qs(context)

        paginator = Paginator(qs, ITEMS_PER_PAGE)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["tickets"] = page_obj
        context["page_obj"] = page_obj
        context["paginator"] = paginator
        return context

    def get_qs(self, context, **kwargs):
        (open_qs, closed_qs) = self.get_query_set()
        status = self.request.GET.get("status", "")
        if status == "open":
            return_qs = open_qs
            context["status"] = "open"
        elif status == "closed":
            return_qs = closed_qs
            context["status"] = "closed"
        else:
            return_qs = open_qs | closed_qs
            context["status"] = ""
        return return_qs.order_by("subject")

    def get_query_set(self, **kwargs):
        qs = self.issue_group.tickets.all()
        open_qs = qs.exclude(status=Ticket.Status.CLOSED)
        closed_qs = qs.filter(status=Ticket.Status.CLOSED)
        return (open_qs, closed_qs)
