from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from django.urls import reverse
from tickets.forms import PasswordForm


class PasswordView(LoginRequiredMixin, FormView):
    """Allow authenticated users to change their password.
    Re-authenticates after a successful update."""

    template_name = "password.html"
    form_class = PasswordForm

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to 'PasswordForm' so it can validate the old password."""

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({"user": self.request.user})
        return kwargs

    def form_valid(self, form):
        """Save the new password and re-authenticate to keep the session alive."""

        form.save()
        login(self.request, self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        """Flash a success message and redirect to the dashboard."""

        messages.add_message(self.request, messages.SUCCESS, "Password updated!")
        return reverse("dashboard")
