from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.contrib import messages
from django.urls import reverse
from tickets.models import User
from tickets.forms import UserForm
from clarify.settings import REDIRECT_URL_WHEN_LOGGED_IN


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Let authenticated users update their own profile information."""

    model = User
    template_name = "profile_edit.html"
    form_class = UserForm

    def get_object(self):
        """Return the request user, ensuring users can only edit their own profile."""
        user = self.request.user
        return user

    def get_success_url(self):
        """Flash a success message and redirect to the logged-in landing page."""
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse(REDIRECT_URL_WHEN_LOGGED_IN)
