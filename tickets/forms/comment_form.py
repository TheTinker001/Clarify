from django import forms
from django_summernote.widgets import SummernoteWidget
from django.utils.html import strip_tags
from tickets.helpers.ticket_files import MultipleFileInput, MultipleFileField
from tickets.models import Comment
from clarify.settings import (
    ALLOWED_EXTENSIONS_ACCEPT,
    ALLOWED_EXTENSIONS_LABEL,
    BODY_LENGTH_MAX,
)


class CommentForm(forms.ModelForm):
    """Form for submitting a comment on a ticket."""

    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": SummernoteWidget()}
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

    def clean_body(self):
        body = self.cleaned_data.get("body", "")
        stripped = strip_tags(body).strip()
        if len(stripped) > BODY_LENGTH_MAX:
            raise forms.ValidationError(
                f"Ensure this value has at most {BODY_LENGTH_MAX} characters (it has {len(stripped)})."
            )
        return body
