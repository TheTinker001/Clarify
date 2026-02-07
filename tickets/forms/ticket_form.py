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
        super().__init__(*args, **kwargs)
        self.fields["subject"].widget.attrs[
            "placeholder"
        ] = "Write your subject here..."
        self.fields["body"].widget.attrs["placeholder"] = "Write your body here..."
