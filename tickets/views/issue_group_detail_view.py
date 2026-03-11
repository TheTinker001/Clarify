from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from tickets.models import User, IssueGroup


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
        return context
