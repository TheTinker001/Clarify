from datetime import timedelta

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from clarify.settings import EDIT_TIME_LIMIT_MINUTES
from tickets.forms import (
    CommentForm,
    TicketPriorityForm,
    InternalNoteForm,
    TicketFieldsForm,
    ReassignTicketForm,
)
from tickets.helpers import _send_staff_comment_email, _send_reassigned_email
from tickets.models import Ticket, User
from tickets.models.attachment import TicketAttachment
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from datetime import timedelta
from django.utils import timezone
from clarify.settings import EDIT_TIME_LIMIT_MINUTES


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

    # GET helpers
    def get_priority_form(self):
        if self.is_staff_user:
            return TicketPriorityForm(instance=self.ticket)
        return None

    def get_comment_form(self):
        return CommentForm()

    def get_fields_form(self):
        if self.is_staff_user:
            return TicketFieldsForm(instance=self.ticket)
        return None

    def get_reassign_form(self):
        if self.is_staff_user and self.ticket.assigned_to_id == self.request.user.id:
            return ReassignTicketForm()
        return None

    # POST function
    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        # Priority update
        if action == "set_priority":
            return self.post_action_set_priority(request, *args, **kwargs)

        # Comment submission
        elif action == "add_comment":
            return self.post_action_add_comment(request, *args, **kwargs)

        # Internal note submission
        elif action == "add_internal_note":
            return self.post_action_add_internal_note(request, *args, **kwargs)

        # Close ticket for being answered
        elif action == "close_ticket":
            return self.post_action_close_ticket(request, *args, **kwargs)

        # Unclose ticket for being unsolved
        elif action == "unclose_ticket":
            return self.post_action_unclose_ticket(request, *args, **kwargs)

        # Edit ticket tags and fields
        elif action == "set_ticket_fields":
            return self.post_action_edit_ticket_fields(request, *args, **kwargs)
        # Reassign ticket to another staff member
        elif action == "reassign_ticket":
            return self.post_action_reassign_ticket(request, *args, **kwargs)
        # Unknown action
        else:
            raise Http404

    # Actions
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

        comment_form = CommentForm(request.POST, request.FILES)
        if comment_form.is_valid():
            files = comment_form.cleaned_data.get("attachments") or []
            if len(files) > TicketAttachment.MAX_FILES_PER_TICKET:
                comment_form.add_error(
                    "attachments",
                    f"You can upload a maximum of {TicketAttachment.MAX_FILES_PER_TICKET} files.",
                )
                return self.render_to_response(self.get_context_data(form=comment_form))

            comment = comment_form.save(commit=False)
            comment.ticket = self.ticket
            comment.author = request.user
            comment.save()

            # Save attachments
            for f in files:
                TicketAttachment.objects.create(comment=comment, file=f)

            if self.is_staff_user:
                try:
                    _send_staff_comment_email(self.ticket, comment)
                except Exception:
                    pass

            # Update ticket status based on commenter
            now = timezone.now()

            if self.ticket.status == Ticket.Status.CLOSED:
                # Student comment reopens the ticket
                if not self.is_staff_user:
                    self.ticket.status = Ticket.Status.AWAITING_STAFF
                    self.ticket.closed_reason = None
                    self.ticket.closed_at = None
                    self.ticket.awaiting_student_since = None
                    self.ticket.save(
                        update_fields=[
                            "status",
                            "closed_reason",
                            "closed_at",
                            "awaiting_student_since",
                            "updated_at",
                        ]
                    )
            else:
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

        # If form is not valid, re-render with errors
        return self.render_to_response(self.get_context_data(form=comment_form))

    def post_action_add_internal_note(self, request, *args, **kwargs):
        if not self.is_staff_user:
            raise Http404

        note_form = InternalNoteForm(request.POST)
        if not note_form.is_valid():
            return self.render_to_response(
                self.get_context_data(internal_note_form=note_form)
            )

        note = note_form.save(commit=False)
        note.ticket = self.ticket
        note.author = request.user
        note.save()

        messages.success(request, "Internal note added.")
        return redirect("ticket_detail", url_code=kwargs.get("url_code"))

    def post_action_close_ticket(self, request, *args, **kwargs):
        if not self.is_staff_user:
            raise Http404

        if self.ticket.assigned_to_id and self.ticket.assigned_to_id != request.user.id:
            raise Http404

        if self.ticket.status == Ticket.Status.CLOSED:
            return redirect("ticket_detail", url_code=kwargs.get("url_code"))

        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.closed_reason = Ticket.ClosedReason.ANSWERED
        self.closed_at = timezone.now()
        self.ticket.awaiting_student_since = None

        self.ticket.save(
            update_fields=[
                "status",
                "closed_reason",
                "closed_at",
                "awaiting_student_since",
                "updated_at",
            ]
        )

        messages.success(request, "Ticket closed as answered.")
        return redirect("ticket_detail", url_code=kwargs.get("url_code"))

    def post_action_unclose_ticket(self, request, *args, **kwargs):
        if not self.is_staff_user:
            raise Http404

        if self.ticket.assigned_to_id and self.ticket.assigned_to_id != request.user.id:
            raise Http404

        if self.ticket.status != Ticket.Status.CLOSED:
            return redirect("ticket_detail", url_code=kwargs.get("url_code"))

        self.ticket.status = Ticket.Status.AWAITING_STAFF
        self.ticket.closed_reason = None
        self.ticket.closed_at = None
        self.ticket.awaiting_student_since = None

        self.ticket.save(
            update_fields=[
                "status",
                "closed_reason",
                "closed_at",
                "awaiting_student_since",
                "updated_at",
            ]
        )

        messages.success(request, "Ticket opened as unsolved.")
        return redirect("ticket_detail", url_code=kwargs.get("url_code"))

    def post_action_reassign_ticket(self, request, *args, **kwargs):
        if not self.is_staff_user:
            raise Http404
        form = ReassignTicketForm(request.POST)
        if form.is_valid():
            reassign = form.cleaned_data.get("reassign")
            if reassign:
                self.ticket.assigned_to = reassign
                self.ticket.save(update_fields=["assigned_to", "updated_at"])
                messages.success(
                    request, f"Ticket forwarded to {reassign.get_full_name()}."
                )

        self.ticket.assigned_to = reassign
        self.ticket.save(update_fields=["assigned_to", "updated_at"])
        _send_reassigned_email(self.ticket, reassign)
        return redirect("ticket_detail", url_code=kwargs.get("url_code"))

    def post_action_edit_ticket_fields(self, request, *args, **kwargs):
        if not self.is_staff_user or self.ticket.status == Ticket.Status.CLOSED:
            raise Http404

        if self.ticket.assigned_to_id and self.ticket.assigned_to_id != request.user.id:
            raise Http404

        fields_form = TicketFieldsForm(request.POST, instance=self.ticket)
        if fields_form.is_valid():
            fields_form.save()
            messages.success(request, "Ticket fields updated.")
        else:
            messages.error(request, "Invalid input for ticket fields.")

        return redirect("ticket_detail", url_code=kwargs.get("url_code"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ticket"] = self.ticket
        context["ticket_priority_form"] = self.get_priority_form()
        context["form"] = kwargs.get("form") or self.get_comment_form()

        now = timezone.now()
        limit = timedelta(minutes=EDIT_TIME_LIMIT_MINUTES)
        comments = list(self.ticket.comments.select_related("author").all())
        for c in comments:
            c.can_edit = (c.author_id == self.request.user.id) and (
                (now - c.created_at) <= limit
            )

        context["comments"] = comments
        if self.is_staff_user:
            context["internal_notes"] = self.ticket.internal_notes.select_related(
                "author"
            ).all()
            context["internal_note_form"] = (
                kwargs.get("internal_note_form") or InternalNoteForm()
            )
            context["ticket_fields_form"] = self.get_fields_form()
            context["reassign_ticket_form"] = ReassignTicketForm()
        return context
