from django import forms
from django_summernote.widgets import SummernoteWidget
from tickets.models.ticket import Ticket


class InternalNoteEditForm(forms.ModelForm):
    """Form for editing the internal notes text block on a ticket."""

    class Meta:
        model = Ticket
        fields = ["internal_notes"]
        widgets = {"internal_notes": SummernoteWidget()}
        labels = {"internal_notes": "Internal Notes"}
