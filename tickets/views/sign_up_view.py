from tickets.views.decorators import LoginProhibitedMixin
from django.views.generic.edit import FormView
from django.contrib.auth import login
from django.urls import reverse
from tickets.models import User
from tickets.forms import SignUpForm
from clarify.settings import REDIRECT_URL_WHEN_LOGGED_IN


class SignUpView(LoginProhibitedMixin, FormView):
    """Display the registration form and create new user accounts.
    Authenticated users are redirected via 'LoginProhibitedMixin'."""

    form_class = SignUpForm
    template_name = "sign_up.html"
    redirect_when_logged_in_url = REDIRECT_URL_WHEN_LOGGED_IN

    def form_valid(self, form):
        """Save the new user, log them in, and proceed to 'get_success_url()'."""
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)

    def get_success_url(self):
        """
        Determine the redirect URL after successful registration.

        Staff users are redirected to their preferences page so they can
        configure which ticket types they want to handle. Students are
        redirected to the dashboard.
        """
        if self.object.user_type == User.USER_TYPE_STAFF:
            return reverse("profile_staff_edit")
        return reverse(REDIRECT_URL_WHEN_LOGGED_IN)
