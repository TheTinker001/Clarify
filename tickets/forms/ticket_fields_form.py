from django import forms
from tickets.models import Ticket


class TicketFieldsForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["faculty", "study_level", "category"]
        widgets = {
            "faculty": forms.Select(attrs={"class": "form-select"}),
            "study_level": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["faculty"].label = "Faculty"
        self.fields["study_level"].label = "Study Level"
        self.fields["category"].label = "Category"
