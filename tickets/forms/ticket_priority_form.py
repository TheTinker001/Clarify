from django import forms
from tickets.models.ticket import Ticket


class TicketPriorityForm(forms.ModelForm):
    """Form used by staff to update the priority of an existing ticket."""

    class Meta:
        model = Ticket
        fields = ["priority"]
        widgets = {
            "priority": forms.Select(attrs={"class": "form-select form-select-sm "}),
        }
