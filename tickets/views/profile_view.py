from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.urls import reverse
from tickets.forms import UserForm, StaffPreferenceForm
from tickets.models import User


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Allow authenticated users to view and update their profile information.

    This class-based view displays a user profile editing form and handles
    updates to the authenticated user’s profile. Access is restricted to
    logged-in users via `LoginRequiredMixin`.
    """

    model = User
    template_name = "profile_edit.html"
    form_class = UserForm

    def get_object(self):
        """
        Retrieve the user object to be edited.

        This ensures that users can only update their own profile, rather
        than any other user’s data.

        Returns:
            User: The currently authenticated user instance.
        """
        user = self.request.user
        return user

    def get_success_url(self):
        """
        Determine the redirect URL after a successful profile update.

        Also adds a success message to inform the user that their profile
        was successfully updated.

        Returns:
            str: The URL to redirect to (typically the dashboard or user home).
        """
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)


class ProfileView(LoginRequiredMixin, UpdateView):

    model = User
    template_name = "profile.html"
    context_object_name = "profile_user"
    form_class = UserForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse("dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        from tickets.models import Ticket

        # Helper to filter and map codes to labels
        def get_labels(codes, choices):
            return [
                choices(code).label for code in codes if code and code in choices.values
            ]

        faculty_codes = (
            [c.strip() for c in user.faculties.split(",") if c.strip()]
            if user.faculties
            else []
        )
        study_level_codes = (
            [c.strip() for c in user.study_levels.split(",") if c.strip()]
            if user.study_levels
            else []
        )
        category_codes = (
            [c.strip() for c in user.categories.split(",") if c.strip()]
            if user.categories
            else []
        )

        context["faculty_list"] = faculty_codes
        context["faculty_labels"] = get_labels(faculty_codes, Ticket.Faculty)
        context["study_level_list"] = study_level_codes
        context["study_level_labels"] = get_labels(study_level_codes, Ticket.StudyLevel)
        context["category_list"] = category_codes
        context["category_labels"] = get_labels(category_codes, Ticket.Category)

        context["Faculty"] = Ticket.Faculty
        context["StudyLevel"] = Ticket.StudyLevel
        context["Category"] = Ticket.Category
        return context


class StaffPreferencesView(LoginRequiredMixin, UpdateView):

    model = User
    template_name = "profile_staff_edit.html"
    context_object_name = "profile_user"
    form_class = StaffPreferenceForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # hide staff-only fields for students
        if self.request.user.user_type != User.USER_TYPE_STAFF:
            form.fields.clear()

        return form

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Preferences updated!")
        return reverse("profile")
