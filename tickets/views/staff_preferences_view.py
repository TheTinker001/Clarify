from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.urls import reverse
from tickets.forms import StaffPreferenceForm
from tickets.models import User
from django.http import Http404


class StaffPreferencesView(LoginRequiredMixin, UpdateView):

    model = User
    template_name = "profile_staff_edit.html"
    context_object_name = "profile_user"
    form_class = StaffPreferenceForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # hide staff-only fields for students
        if self.request.user.user_type != User.USER_TYPE_STAFF:
            form.fields.clear()

        return form

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Preferences updated!")
        return reverse("profile")

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type != User.USER_TYPE_STAFF:
            raise Http404("Page not found")
        return super().dispatch(request, *args, **kwargs)
