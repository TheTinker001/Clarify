from django import forms
from tickets.models import Ticket


class TicketForm(forms.ModelForm):

    class Meta:
        model = Ticket
        fields = ["faculty", "study_level", "category", "subject", "body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 10}),
        }

    def __init__(self, *args, **kwargs):
        kwargs["label_suffix"] = " *"
        super().__init__(*args, **kwargs)

        self.fields["faculty"].label = "Please select your faculty"
        self.fields["study_level"].label = "Please select the relevant level of study"
        self.fields["category"].label = "What is your question about? "
        self.fields["subject"].label = "Let us know why you're getting in touch"
        self.fields["body"].label = "Please provide more details"

        self.fields["subject"].widget.attrs[
            "placeholder"
        ] = "Write your subject here..."
        self.fields["body"].widget.attrs["placeholder"] = "Write your body here..."
