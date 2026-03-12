from django.views.generic import UpdateView
from tickets.models import User, IssueGroup
from django.contrib import messages
from django.shortcuts import redirect


class UpdateIssueGroupView(UpdateView):
    model = IssueGroup
    fields = ["name"]
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "issue_group_edit.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type != User.USER_TYPE_STAFF:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Issue group name updated successfully.")
        return super().form_valid(form)
