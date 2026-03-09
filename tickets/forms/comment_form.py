from django import forms

from tickets.models import Comment
from tickets.helpers import MultipleFileInput, MultipleFileField
from clarify.settings import ALLOWED_EXTENSIONS_ACCEPT, ALLOWED_EXTENSIONS_LABEL


class CommentForm(forms.ModelForm):
    """Form for submitting a comment on a ticket."""

    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Write a comment..."}
            ),
        }
        labels = {
            "body": "",
        }

    attachments = MultipleFileField(
        widget=MultipleFileInput(
            attrs={
                "accept": ALLOWED_EXTENSIONS_ACCEPT,
            }
        ),
        required=False,
        label=ALLOWED_EXTENSIONS_LABEL,
    )
