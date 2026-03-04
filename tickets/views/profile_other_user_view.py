from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from tickets.models import User
from tickets.views.profile_view import UserProfileContext


class ProfileOtherUserView(LoginRequiredMixin, UserProfileContext, DetailView):
    model = User
    template_name = "profile_other_user.html"
    context_object_name = "profile_user"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_profile_context(context["profile_user"]))
        return context
