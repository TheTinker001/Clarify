from django import forms
from django.utils.html import strip_tags

from tickets.models import Ticket
from tickets.helpers import MultipleFileInput, MultipleFileField
from clarify.settings import (
    ALLOWED_EXTENSIONS_ACCEPT,
    ALLOWED_EXTENSIONS_LABEL,
    BODY_LENGTH_MAX,
)
from django_summernote.widgets import SummernoteWidget


class TicketForm(forms.ModelForm):
    """Form for creating a ticket."""

    class Meta:
        model = Ticket
        fields = ["faculty", "study_level", "category", "priority", "subject", "body"]
        widgets = {
            "body": SummernoteWidget(),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["faculty"].label = "Please select your faculty"
        self.fields["study_level"].label = "Please select the relevant level of study"
        self.fields["category"].label = "What is your question about?"
        self.fields["priority"].label = "How urgent is your issue?"
        self.fields["subject"].label = "Let us know why you're getting in touch"
        self.fields["subject"].widget.attrs[
            "placeholder"
        ] = "Write your subject here..."
        self.fields["body"].label = "Please provide more details"
        self.fields["body"].widget.attrs["placeholder"] = "Write your body here..."

    def clean_attachments(self):
        """Return the validated attachments list"""
        return self.cleaned_data.get("attachments")

    def clean_body(self):
        body = self.cleaned_data.get("body", "")
        stripped = strip_tags(body).strip()
        if len(stripped) > BODY_LENGTH_MAX:
            raise forms.ValidationError(
                f"Ensure this value has at most {BODY_LENGTH_MAX} characters (it has {len(stripped)})."
            )
        return body
