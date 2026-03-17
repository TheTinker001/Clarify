from django import forms

from tickets.models.ticket import Ticket


class InternalNoteEditForm(forms.ModelForm):
    """Form for editing the internal notes text block on a ticket."""

    class Meta:
        model = Ticket
        fields = ["internal_notes"]
        widgets = {
            "internal_notes": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Write internal notes here..."}
            )
        }
        labels = {"internal_notes": "Internal Notes"}
