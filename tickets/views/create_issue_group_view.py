from django.shortcuts import redirect
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from tickets.models import IssueGroup
from tickets.forms import IssueGroupForm


class CreateIssueGroupView(LoginRequiredMixin, CreateView):

    model = IssueGroup
    form_class = IssueGroupForm
    template_name = "create_issue_group.html"
    success_url = reverse_lazy("issue_group")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.user_type == "student":
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Issue group created successfully!")
        return response
