from django import forms
from tickets.models import Ticket
from tickets.helpers import MultipleFileInput, MultipleFileField


class TicketForm(forms.ModelForm):
    """
    Form for creating a support ticket.

    ``attachments`` is a non-model field; the view saves files as ``TicketAttachment``
    rows after the ticket is created.
    """

    class Meta:
        model = Ticket
        fields = ["faculty", "study_level", "category", "subject", "body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 10}),
        }

    attachments = MultipleFileField(
        widget=MultipleFileInput(
            attrs={
                "accept": ".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png",
            }
        ),
        required=False,
        label="Attachments (max 5 files, 5MB each — pdf, doc, docx, txt, jpg, jpeg, png)",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["faculty"].label = "Please select your faculty"
        self.fields["study_level"].label = "Please select the relevant level of study"
        self.fields["category"].label = "What is your question about?"
        self.fields["subject"].label = "Let us know why you're getting in touch"
        self.fields["subject"].widget.attrs[
            "placeholder"
        ] = "Write your subject here..."

        self.fields["body"].label = "Please provide more details"
        self.fields["body"].widget.attrs["placeholder"] = "Write your body here..."

    def clean_attachments(self):
        """Return the validated attachments list (per-file validation is handled by MultipleFileField)."""
        return self.cleaned_data.get("attachments")
