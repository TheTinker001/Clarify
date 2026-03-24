from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from tickets.models import Ticket, User


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
