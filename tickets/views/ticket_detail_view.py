from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from tickets.forms import CommentForm, TicketPriorityForm
from tickets.models import Ticket, User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from django.utils import timezone


class TicketDetailView(LoginRequiredMixin, TemplateView):
    """Display a single ticket, handle priority and handle comment submission."""

    template_name = "ticket_detail.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        self.ticket = get_object_or_404(
            Ticket.objects.select_related("student", "assigned_to"),
            url_code=kwargs.get("url_code"),
        )

        self.is_staff_user = request.user.user_type == User.USER_TYPE_STAFF
        self.is_owner = self.ticket.student_id == request.user.id

        # Permission check
        if not (self.is_staff_user or self.is_owner):
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_priority_form(self):
        # Default forms for GET
        if self.is_staff_user:
            return TicketPriorityForm(instance=self.ticket)
        return None

    def get_comment_form(self):
        # Default forms for GET
        return CommentForm()

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        # Priority update
        if action == "set_priority":
            return self.post_action_set_priority(request, *args, **kwargs)

        # Comment submission
        elif action == "add_comment":
            return self.post_action_add_comment(request, *args, **kwargs)

        # Close ticket for being answered
        elif action == "close_ticket":
            return self.post_action_close_ticket(request, *args, **kwargs)

        # Unknown action
        else:
            raise Http404

    def post_action_set_priority(self, request, *args, **kwargs):
        if not self.is_staff_user or self.ticket.status == Ticket.Status.CLOSED:
            raise Http404

        priority_form = TicketPriorityForm(request.POST, instance=self.ticket)
        if priority_form.is_valid():
            priority_form.save()
            messages.success(request, "Priority updated.")
        else:
            messages.error(request, "Invalid priority.")

        return redirect("ticket_detail", url_code=kwargs.get("url_code"))

    def post_action_add_comment(self, request, *args, **kwargs):
        if self.is_staff_user and self.ticket.assigned_to_id != request.user.id:
            raise Http404

        comment_form = CommentForm(request.POST)

        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = self.ticket
            comment.author = request.user
            comment.save()

            # Update ticket status based on commenter (unless closed)
            if self.ticket.status != Ticket.Status.CLOSED:
                now = timezone.now()

                if self.is_staff_user:
                    self.ticket.status = Ticket.Status.AWAITING_STUDENT
                    self.ticket.awaiting_student_since = now
                else:
                    self.ticket.status = Ticket.Status.AWAITING_STAFF
                    self.ticket.awaiting_student_since = None

                self.ticket.save(
                    update_fields=["status", "awaiting_student_since", "updated_at"]
                )

            messages.success(request, "Comment added.")
            return redirect("ticket_detail", url_code=kwargs.get("url_code"))

        return self.render_to_response(self.get_context_data(form=comment_form))

    def post_action_close_ticket(self, request, *args, **kwargs):
        if not self.is_staff_user:
            raise Http404

        if self.ticket.assigned_to_id and self.ticket.assigned_to_id != request.user.id:
            raise Http404

        if self.ticket.status == Ticket.Status.CLOSED:
            return redirect("ticket_detail", url_code=kwargs.get("url_code"))

        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.ticket.awaiting_student_since = None

        self.ticket.save(
            update_fields=[
                "status",
                "closed_reason",
                "awaiting_student_since",
                "updated_at",
                "closed_at",
            ]
        )

        messages.success(request, "Ticket closed as answered.")
        return redirect("ticket_detail", url_code=kwargs.get("url_code"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ticket"] = self.ticket
        context["ticket_priority_form"] = self.get_priority_form()
        context["form"] = kwargs.get("form", self.get_comment_form())
        context["comments"] = self.ticket.comments.select_related("author").all()
        return context
