from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.http import Http404
from tickets.models import User, Ticket
from tickets.forms import InternalNoteEditForm


class InternalNoteEditView(LoginRequiredMixin, UpdateView):
    """Allow a superuser or claiming staff member to edit a ticket's internal notes."""

    model = Ticket
    form_class = InternalNoteEditForm
    template_name = "internal_note_edit.html"
    slug_field = "url_code"
    slug_url_kwarg = "url_code"

    def dispatch(self, request, *args, **kwargs):
        """Check permissions before processing the request."""
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        self.object = self.get_object()

        if (
            not request.user.is_superuser
            and request.user.user_type != User.USER_TYPE_STAFF
        ):
            raise Http404

        if (
            not request.user.is_superuser
            and not self.object.assigned_to.filter(id=request.user.id).exists()
        ):
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """Redirect to the ticket detail page after a successful save."""
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        """Add the ticket to context."""
        context = super().get_context_data(**kwargs)
        context["ticket"] = self.object
        return context
