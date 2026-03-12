from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from tickets.models import User, IssueGroup
from django.core.paginator import Paginator

from clarify.settings import ITEMS_PER_PAGE


class IssueGroupView(LoginRequiredMixin, TemplateView):

    template_name = "issue_group.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type != User.USER_TYPE_STAFF:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = IssueGroup.objects.all().order_by("name")

        paginator = Paginator(qs, ITEMS_PER_PAGE)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["issue_groups"] = page_obj
        context["page_obj"] = page_obj
        context["paginator"] = paginator
        return context
