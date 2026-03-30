from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from django.http import Http404
from django.contrib import messages
from django.urls import reverse_lazy
from tickets.helpers import _send_ticket_created_email
from tickets.models import Ticket, TicketAttachment
from tickets.forms import TicketForm
from clarify.settings import MAX_FILES_PER_TICKET, TICKET_EDIT_WINDOW_MINUTES


class CreateTicketView(LoginRequiredMixin, CreateView):
    """
    Let students submit a new ticket. Staff are redirected away.

    Attachments are saved as 'TicketAttachment' rows after the ticket is created.
    """

    model = Ticket
    form_class = TicketForm
    template_name = "create_ticket.html"
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        """Redirect non-student users to the dashboard before any form processing."""
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.user_type != "student":
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Save the ticket and attachments, send a confirmation email (failures silently swallowed)."""
        form.instance.student = self.request.user
        files = self.request.FILES.getlist("attachments")
        if len(files) > MAX_FILES_PER_TICKET:
            form.add_error(
                "attachments",
                f"You can upload a maximum of {MAX_FILES_PER_TICKET} files.",
            )
            return self.form_invalid(form)

        response = super().form_valid(form)

        for f in files:
            TicketAttachment.objects.create(ticket=self.object, file=f)

        try:
            _send_ticket_created_email(self.object)
        except Exception:
            pass

        messages.success(
            self.request,
            f"Ticket created successfully! You have {TICKET_EDIT_WINDOW_MINUTES} minutes to edit/delete your ticket.",
        )
        return response
