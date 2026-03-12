from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from tickets.models import User, IssueGroup
from django.core.paginator import Paginator

from clarify.settings import ITEMS_PER_PAGE


class IssueGroupDetailView(LoginRequiredMixin, TemplateView):
    template_name = "issue_group_detail.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type != User.USER_TYPE_STAFF:
            return redirect("dashboard")

        self.issue_group = get_object_or_404(IssueGroup, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["issue_group"] = self.issue_group

        paginator = Paginator(self.issue_group.tickets.all(), ITEMS_PER_PAGE)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["tickets"] = page_obj
        context["page_obj"] = page_obj
        context["paginator"] = paginator
        return context
