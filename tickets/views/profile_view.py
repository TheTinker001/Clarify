from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.urls import reverse
from tickets.forms import UserForm
from tickets.models import User


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
