from django import forms
from tickets.models import User, Ticket


class StaffPreferenceForm(forms.ModelForm):
    """
    Form enabling staff users to set their ticket handling preferences.

    This form allows staff members to select the faculties, study levels,
    and categories of tickets they are willing to handle. It is typically
    used in a staff profile or settings page.
    """

    faculties = forms.MultipleChoiceField(
        choices=Ticket.Faculty.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    study_levels = forms.MultipleChoiceField(
        choices=Ticket.StudyLevel.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    categories = forms.MultipleChoiceField(
        choices=Ticket.Category.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        """Form options."""

        model = User
        fields = ["faculties", "study_levels", "categories"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert comma-separated string to list for initial display
        self.fields["faculties"].initial = (
            self.instance.faculties.split(",") if self.instance.faculties else []
        )
        self.fields["study_levels"].initial = (
            self.instance.study_levels.split(",") if self.instance.study_levels else []
        )
        self.fields["categories"].initial = (
            self.instance.categories.split(",") if self.instance.categories else []
        )

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
