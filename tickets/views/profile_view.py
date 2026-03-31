from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.contrib import messages
from django.urls import reverse
from tickets.models import User, Ticket
from tickets.forms import UserForm


class UserProfileContext:
    """Mixin that converts a user's CSV preference fields into labels and 'all selected' flags for templates."""

    def get_profile_context(self, user):
        """Return context with preference codes, human-readable labels, and 'all selected' flags."""

        def get_labels(codes, choices):
            """Map choice codes to labels, silently skipping any stale codes not in the enum."""
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

        return {
            "faculty_list": faculty_codes,
            "faculty_labels": get_labels(faculty_codes, Ticket.Faculty),
            "all_faculties_selected": len(faculty_codes)
            == len(Ticket.Faculty.choices) - 1,
            "study_level_list": study_level_codes,
            "study_level_labels": get_labels(study_level_codes, Ticket.StudyLevel),
            "all_study_levels_selected": len(study_level_codes)
            == len(Ticket.StudyLevel.choices) - 1,
            "category_list": category_codes,
            "category_labels": get_labels(category_codes, Ticket.Category),
            "all_categories_selected": len(category_codes)
            == len(Ticket.Category.choices) - 1,
            "Faculty": Ticket.Faculty,
            "StudyLevel": Ticket.StudyLevel,
            "Category": Ticket.Category,
        }


class ProfileView(LoginRequiredMixin, UserProfileContext, UpdateView):
    """Edit the current user's own profile. 'get_object' always returns the request user to prevent URL manipulation."""

    model = User
    template_name = "profile.html"
    context_object_name = "profile_user"
    form_class = UserForm

    def get_context_data(self, **kwargs):
        """Add preference labels and 'all selected' flags to the template context."""
        context = super().get_context_data(**kwargs)
        context.update(self.get_profile_context(self.request.user))
        return context

    def get_object(self, queryset=None):
        """Always return the request user, preventing access to other profiles via URL."""
        return self.request.user

    def get_success_url(self):
        """Flash a success message and redirect to the dashboard."""
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse("dashboard")
