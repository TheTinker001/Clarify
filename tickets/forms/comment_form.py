from django import forms

from tickets.models import Comment


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
