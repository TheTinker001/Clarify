from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic.edit import UpdateView

from tickets.forms import TicketForm
from tickets.models import Ticket, User


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

    def get_success_url(self):
        messages.success(self.request, "Ticket updated successfully.")
        return self.object.get_absolute_url()


class DeleteTicketView(LoginRequiredMixin, View):
    """Allow students to delete their ticket within the edit window."""

    http_method_names = ["post"]

    def post(self, request, url_code):
        ticket = get_object_or_404(Ticket, url_code=url_code)

        if request.user.user_type != User.USER_TYPE_STUDENT:
            raise Http404
        if ticket.student_id != request.user.id:
            raise Http404
        if not ticket.is_editable_by_student():
            messages.error(request, "The delete window for this ticket has expired.")
            return redirect(ticket.get_absolute_url())

        ticket.delete()
        messages.success(request, "Ticket deleted.")
        return redirect("dashboard")
