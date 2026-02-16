from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.urls import reverse
from tickets.forms import UserForm
from tickets.models import User, Ticket
from django.views.generic import DetailView


class UserProfileContext:
    def get_profile_context(self, user):

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
    model = User
    template_name = "profile.html"
    context_object_name = "profile_user"
    form_class = UserForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_profile_context(self.request.user))
        return context

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse("dashboard")
