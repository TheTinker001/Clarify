from django import forms
from tickets.models.ticket import Ticket


class TicketPriorityForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["priority"]
        widgets = {
            "priority": forms.Select(attrs={"class": "form-select form-select-sm "}),
        }
