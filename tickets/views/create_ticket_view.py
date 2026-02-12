from django.shortcuts import redirect
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from tickets.models import Ticket
from tickets.forms import TicketForm
from tickets.helpers import _send_ticket_created_email


class CreateTicketView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    template_name = "create_ticket.html"
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.user_type != "student":
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.student = self.request.user
        response = super().form_valid(form)

        try:
            _send_ticket_created_email(self.object)
        except Exception:
            pass

        messages.success(self.request, "Ticket created successfully!")
        return response
