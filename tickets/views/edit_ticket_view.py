from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.edit import UpdateView

from tickets.forms import TicketForm
from tickets.models import Ticket, User
from tickets.models.attachment import TicketAttachment
from clarify.settings import MAX_FILES_PER_TICKET


class EditTicketView(LoginRequiredMixin, UpdateView):
    """Allow students to edit their ticket within the edit window."""

    model = Ticket
    form_class = TicketForm
    template_name = "edit_ticket.html"
    slug_field = "url_code"
    slug_url_kwarg = "url_code"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        self.object = get_object_or_404(Ticket, url_code=kwargs.get("url_code"))

        if request.user.user_type != User.USER_TYPE_STUDENT:
            raise Http404
        if self.object.student_id != request.user.id:
            raise Http404
        if not self.object.is_editable_by_student():
            messages.error(request, "The edit window for this ticket has expired.")
            return redirect(self.object.get_absolute_url())

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        files = self.request.FILES.getlist("attachments")

        if self.object.attachments.count() + len(files) > MAX_FILES_PER_TICKET:
            form.add_error(
                "attachments",
                f"You can upload a maximum of {MAX_FILES_PER_TICKET} files.",
            )
            return self.form_invalid(form)

        response = super().form_valid(form)

        for f in files:
            TicketAttachment.objects.create(ticket=self.object, file=f)

        return response

    def get_success_url(self):
        messages.success(self.request, "Ticket updated successfully.")
        return self.object.get_absolute_url()
