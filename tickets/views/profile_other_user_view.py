from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import DetailView
from tickets.models import User
from tickets.views.profile_view import UserProfileContext


class ProfileOtherUserView(LoginRequiredMixin, UserProfileContext, DetailView):
    """Read-only profile view for other users, looked up by 'username' slug."""

    model = User
    template_name = "profile_other_user.html"
    context_object_name = "profile_user"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_object(self, queryset=None):
        """Restrict student viewers to staff profiles (and their own profile only)."""
        profile_user = super().get_object(queryset)
        viewer = self.request.user

        if viewer.user_type == User.USER_TYPE_STAFF:
            return profile_user

        if viewer.pk == profile_user.pk:
            return profile_user

        if profile_user.user_type == User.USER_TYPE_STAFF:
            return profile_user

        raise Http404("Page not found")

    def get_context_data(self, **kwargs):
        """Add ticket-preference context and visibility flags for the viewed user."""
        context = super().get_context_data(**kwargs)
        profile_user = context["profile_user"]
        viewer = self.request.user
        context.update(self.get_profile_context(profile_user))
        context["can_view_email"] = (
            viewer.user_type == User.USER_TYPE_STAFF or viewer.pk == profile_user.pk
        )
        context["can_view_student_details"] = (
            profile_user.user_type == User.USER_TYPE_STUDENT
            and (
                viewer.user_type == User.USER_TYPE_STAFF or viewer.pk == profile_user.pk
            )
        )
        return context
