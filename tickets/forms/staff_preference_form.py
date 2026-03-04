from django import forms
from tickets.models import User, Ticket


def _split_codes(value: str):
    return [c.strip() for c in value.split(",") if c.strip()]


def _no_empty(choices):
    return [(v, label) for v, label in choices if v]


class StaffPreferenceForm(forms.ModelForm):
    """
    Form enabling staff users to set their ticket handling preferences.

    This form allows staff members to select the faculties, study levels,
    and categories of tickets they are willing to handle. It is typically
    used in a staff profile or settings page.
    """

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
        super().__init__(*args, **kwargs)

        if self.instance.faculties:
            self.initial["faculties"] = _split_codes(self.instance.faculties)
        if self.instance.study_levels:
            self.initial["study_levels"] = _split_codes(self.instance.study_levels)
        if self.instance.categories:
            self.initial["categories"] = _split_codes(self.instance.categories)

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.user_type != User.USER_TYPE_STAFF:
            raise forms.ValidationError("Only staff can edit preferences.")
        return cleaned_data

    def clean_faculties(self):
        return ",".join(self.cleaned_data["faculties"])

    def clean_study_levels(self):
        return ",".join(self.cleaned_data["study_levels"])

    def clean_categories(self):
        return ",".join(self.cleaned_data["categories"])

    class Meta:
        """Form options."""

        model = User
        fields = ["faculties", "study_levels", "categories"]
