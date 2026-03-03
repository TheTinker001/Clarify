from django import forms

from tickets.models import InternalNote


class InternalNoteForm(forms.ModelForm):
    """Form for submitting an internal note on a ticket."""

    class Meta:
        model = InternalNote
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Add an internal note..."}
            ),
        }
        labels = {
            "body": "",
        }
