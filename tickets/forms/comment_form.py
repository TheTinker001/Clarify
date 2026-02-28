from django import forms

from tickets.models import Comment
from tickets.helpers import MultipleFileInput, MultipleFileField


class CommentForm(forms.ModelForm):
    """Form for submitting a comment on a ticket."""

    attachments = MultipleFileField(
        widget=MultipleFileInput(
            attrs={
                "accept": ".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png",
            }
        ),
        required=False,
        label="Attachments (max 5 files, 5MB each — pdf, doc, docx, txt, jpg, jpeg, png)",
    )

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
