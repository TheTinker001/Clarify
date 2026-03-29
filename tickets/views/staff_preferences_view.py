from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.urls import reverse
from tickets.forms import StaffPreferenceForm
from tickets.models import User
from django.http import Http404


class StaffPreferencesView(LoginRequiredMixin, UpdateView):
    """Let staff configure ticket-handling preferences. Non-staff get a 404 to avoid revealing the URL."""

    model = User
    template_name = "profile_staff_edit.html"
    context_object_name = "profile_user"
    form_class = StaffPreferenceForm

    def get_object(self, queryset=None):
        """Return the currently authenticated user as the object to update."""
        return self.request.user

    def get_form(self, form_class=None):
        """Return the form, clearing fields for non-staff users."""
        form = super().get_form(form_class)

        if self.request.user.user_type != User.USER_TYPE_STAFF:
            form.fields.clear()

        return form

    def get_success_url(self):
        """Redirect to the profile page and show a success notification."""
        messages.add_message(self.request, messages.SUCCESS, "Preferences updated!")
        return reverse("profile")

    def dispatch(self, request, *args, **kwargs):
        """Raise Http404 for non-staff to avoid disclosing the URL to students."""
        if (
            not request.user.is_authenticated
            or request.user.user_type != User.USER_TYPE_STAFF
        ):
            raise Http404("Page not found")
        return super().dispatch(request, *args, **kwargs)
