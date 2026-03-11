from django.views.generic import UpdateView
from tickets.models import IssueGroup
from django.contrib import messages


class UpdateIssueGroupView(UpdateView):
    model = IssueGroup
    fields = ["name"]
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "issue_group_edit.html"

    def form_valid(self, form):
        messages.success(self.request, "Issue group name updated successfully.")
        return super().form_valid(form)
