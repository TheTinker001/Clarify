from django.shortcuts import redirect
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from tickets.models import Ticket
from tickets.forms import TicketForm
from tickets.helpers import _send_ticket_created_email
from tickets.models.attachment import TicketAttachment


class CreateTicketView(LoginRequiredMixin, CreateView):
    """
    Let students submit a new ticket. Staff are redirected away.

    Attachments are saved as ``TicketAttachment`` rows after the ticket is created.
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
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Save the ticket and attachments, send a confirmation email (failures silently swallowed)."""
        form.instance.student = self.request.user
        files = self.request.FILES.getlist("attachments")
        if len(files) > TicketAttachment.MAX_FILES_PER_TICKET:
            form.add_error(
                "attachments",
                f"You can upload a maximum of {TicketAttachment.MAX_FILES_PER_TICKET} files.",
            )
            return self.form_invalid(form)

        response = super().form_valid(form)

        for f in files:
            TicketAttachment.objects.create(ticket=self.object, file=f)

        try:
            _send_ticket_created_email(self.object)
        except Exception:
            pass

        messages.success(self.request, "Ticket created successfully!")
        return response
