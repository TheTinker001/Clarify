from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect


def login_prohibited(view_function):
    """Redirect authenticated users to ``REDIRECT_URL_WHEN_LOGGED_IN``; otherwise call the original view."""
    
    def modified_view_function(request):
        if request.user.is_authenticated:
            return redirect(settings.REDIRECT_URL_WHEN_LOGGED_IN)
        else:
            return view_function(request)
    return modified_view_function


class LoginProhibitedMixin:
    """Redirect authenticated users away from views they should not reach (e.g. login, signup)."""

    redirect_when_logged_in_url = None

    def dispatch(self, *args, **kwargs):
        """Redirect authenticated users via ``handle_already_logged_in``."""
        if self.request.user.is_authenticated:
            return self.handle_already_logged_in(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def handle_already_logged_in(self, *args, **kwargs):
        """Resolve the redirect URL and issue the redirect."""
        url = self.get_redirect_when_logged_in_url()
        return redirect(url)

    def get_redirect_when_logged_in_url(self):
        """Return ``redirect_when_logged_in_url``, raising ``ImproperlyConfigured`` if it is unset."""
        if self.redirect_when_logged_in_url is None:
            raise ImproperlyConfigured(
                "LoginProhibitedMixin requires either a value for "
                "'redirect_when_logged_in_url', or an implementation for "
                "'get_redirect_when_logged_in_url()'."
            )
        else:
            return self.redirect_when_logged_in_url