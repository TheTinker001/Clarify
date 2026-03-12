from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import DetailView
from tickets.models import User
from tickets.views.profile_view import UserProfileContext


class ProfileOtherUserView(LoginRequiredMixin, UserProfileContext, DetailView):
    """Read-only profile view for another user, looked up by username slug.

    Access rules:
    - Staff can view any profile.
    - Students can view staff profiles (but email is hidden in the template).
    - Students cannot view other students' profiles (raises 403).
    """

    model = User
    template_name = "profile_other_user.html"
    context_object_name = "profile_user"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_object(self, queryset=None):
        """Return the profile user, raising 403 if a student tries to view another student."""
        profile_user = super().get_object(queryset)
        viewer = self.request.user
        if (
            viewer.user_type == User.USER_TYPE_STUDENT
            and profile_user.user_type == User.USER_TYPE_STUDENT
            and viewer.pk != profile_user.pk
        ):
            raise PermissionDenied
        return profile_user

    def get_context_data(self, **kwargs):
        """Add preference context and hide_email flag for student viewers."""
        context = super().get_context_data(**kwargs)
        context.update(self.get_profile_context(context["profile_user"]))
        context["hide_email"] = self.request.user.user_type == User.USER_TYPE_STUDENT
        return context
