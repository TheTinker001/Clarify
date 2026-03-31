from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from tickets.views.decorators import login_prohibited


@method_decorator(login_prohibited, name="dispatch")
class HomeView(TemplateView):
    """Display the application's start/home screen."""

    template_name = "home.html"
