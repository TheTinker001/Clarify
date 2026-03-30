from django import forms
from tickets.models import IssueGroup


class IssueGroupForm(forms.ModelForm):
    """Form for creating an issue group."""

    class Meta:
        model = IssueGroup
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].label = "Please provide a name for the issue group"
        self.fields["name"].widget.attrs[
            "placeholder"
        ] = "Write the issue group name here..."
