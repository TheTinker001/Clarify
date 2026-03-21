from django import forms
from tickets.models import Ticket, IssueGroup


class TicketIssueGroupForm(forms.ModelForm):
    """Form used by staff to update the issue group of an existing ticket."""

    class Meta:
        model = Ticket
        fields = ["issue_group"]

    issue_group = forms.ModelChoiceField(
        queryset=IssueGroup.objects.filter(is_archived=False),
        required=False,
        empty_label="No Issue Group",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
