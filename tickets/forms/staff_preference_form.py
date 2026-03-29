from django import forms
from tickets.models import User, Ticket


def _split_codes(value: str):
    """Split a comma-separated preference string into a stripped, non-empty list."""
    return [c.strip() for c in value.split(",") if c.strip()]


def _no_empty(choices):
    """Strip the EMPTY sentinel entry from a TextChoices list before use as checkbox options."""
    return [(v, label) for v, label in choices if v]


class StaffPreferenceForm(forms.ModelForm):
    """Let staff select the faculties, study levels, and categories of tickets they handle."""

    class Meta:
        """Form options."""

        model = User
        fields = ["faculties", "study_levels", "categories"]

    faculties = forms.MultipleChoiceField(
        choices=_no_empty(Ticket.Faculty.choices),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "faculty-checkbox"}),
    )
    study_levels = forms.MultipleChoiceField(
        choices=_no_empty(Ticket.StudyLevel.choices),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "study-level-checkbox"}),
    )
    categories = forms.MultipleChoiceField(
        choices=_no_empty(Ticket.Category.choices),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "category-checkbox"}),
    )

    def __init__(self, *args, **kwargs):
        """Pre-populate checkbox selections by splitting the stored CSV preference strings."""
        super().__init__(*args, **kwargs)

        all_faculties = [code for code, _ in _no_empty(Ticket.Faculty.choices)]
        all_study_levels = [code for code, _ in _no_empty(Ticket.StudyLevel.choices)]
        all_categories = [code for code, _ in _no_empty(Ticket.Category.choices)]

        self.initial["faculties"] = (
            _split_codes(self.instance.faculties)
            if self.instance.faculties
            else all_faculties
        )
        self.initial["study_levels"] = (
            _split_codes(self.instance.study_levels)
            if self.instance.study_levels
            else all_study_levels
        )
        self.initial["categories"] = (
            _split_codes(self.instance.categories)
            if self.instance.categories
            else all_categories
        )

    def clean(self):
        """Reject the form if the bound user is not a staff member."""
        cleaned_data = super().clean()
        if self.instance.user_type != User.USER_TYPE_STAFF:
            raise forms.ValidationError("Only staff can edit preferences.")
        return cleaned_data

    def clean_faculties(self):
        """Re-join the validated list of faculty codes into a comma-separated string for storage."""
        return ",".join(self.cleaned_data["faculties"])

    def clean_study_levels(self):
        """Re-join the validated list of study-level codes into a comma-separated string for storage."""
        return ",".join(self.cleaned_data["study_levels"])

    def clean_categories(self):
        """Re-join the validated list of category codes into a comma-separated string for storage."""
        return ",".join(self.cleaned_data["categories"])
