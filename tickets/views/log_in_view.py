from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views import View
from tickets.forms import LogInForm
from tickets.views.decorators import LoginProhibitedMixin


class LogInView(LoginProhibitedMixin, View):
    """Display and process the login form.
    Authenticated users are redirected via 'LoginProhibitedMixin'."""

    http_method_names = ["get", "post"]
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def get(self, request):
        """Render the login form."""

        self.next = request.GET.get("next") or ""
        return self.render()

    def post(self, request):
        """Authenticate the submitted credentials.
        Redirect on success or re-render with an error."""

        form = LogInForm(request.POST)
        self.next = request.POST.get("next") or settings.REDIRECT_URL_WHEN_LOGGED_IN
        user = form.get_user()
        if user is not None:
            login(request, user)
            return redirect(self.next)
        messages.add_message(
            request, messages.ERROR, "The credentials provided were invalid!"
        )
        return self.render()

    def render(self):
        """Render the login template with a blank form."""

        form = LogInForm()
        return render(self.request, "log_in.html", {"form": form, "next": self.next})
