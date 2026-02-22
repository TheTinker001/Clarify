from django import forms
from tickets.models.ticket_response import TicketResponse


class TicketResponseForm(forms.ModelForm):
    """Form for submitting a response to a ticket."""

    class Meta:
        model = TicketResponse
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Write your response...",
                "class": "form-control",
            }),
        }
        labels = {
            "body": "Response",
        }
