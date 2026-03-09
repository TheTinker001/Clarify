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
)
from tickets.helpers import _send_staff_comment_email
from tickets.models import Ticket, User
from tickets.models.attachment import TicketAttachment


class TicketDetailView(LoginRequiredMixin, TemplateView):
    """
    Display a ticket and handle all in-page form submissions.

    POST is dispatched via an 'action' field: 'set_priority', 'add_comment',
    'add_internal_note', 'close_ticket', 'unclose_ticket'.

    'dispatch' sets 'self.ticket', 'self.is_staff_user', and 'self.is_owner'.
    """

    template_name = "ticket_detail.html"

    def dispatch(self, request, *args, **kwargs):
        """Fetch the ticket with 'select_related' and enforce owner-or-staff access."""
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        self.ticket = get_object_or_404(
            Ticket.objects.select_related("student", "assigned_to"),
            url_code=kwargs.get("url_code"),
        )

        self.is_staff_user = request.user.user_type == User.USER_TYPE_STAFF
        self.is_owner = self.ticket.student_id == request.user.id

        # Only the ticket's student or any staff member may access this page.
        if not (self.is_staff_user or self.is_owner):
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    # GET helpers
    def get_priority_form(self):
        """Return a pre-populated priority form for staff, or None for students."""
        if self.is_staff_user:
            return TicketPriorityForm(instance=self.ticket)
        return None

    def get_comment_form(self):
        """Return a blank comment form."""
        return CommentForm()

    # POST dispatcher
    def post(self, request, *args, **kwargs):
        """Dispatch to the correct action handler.
        Raises Http404 for unrecognised action values."""
        action = request.POST.get("action")

        if action == "set_priority":
            return self.post_action_set_priority(request, *args, **kwargs)

        elif action == "add_comment":
            return self.post_action_add_comment(request, *args, **kwargs)

        elif action == "add_internal_note":
            return self.post_action_add_internal_note(request, *args, **kwargs)

        elif action == "close_ticket":
            return self.post_action_close_ticket(request, *args, **kwargs)

        elif action == "unclose_ticket":
            return self.post_action_unclose_ticket(request, *args, **kwargs)

        raise Http404

    # Action handlers
    def post_action_set_priority(self, request, *args, **kwargs):
        """Update the ticket's priority for staff.
        Raises Http404 on closed tickets."""
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
        """
        Save a public comment and advance the ticket's status.

        Staff comment sets the ticket's status to AWAITING_STUDENT
        Student comment sets the ticket's status to AWAITING_STAFF (reopens the ticket if closed).
        Staff may only comment on tickets assigned to them.
        """
        if self.is_staff_user and self.ticket.assigned_to_id != request.user.id:
            raise Http404

        comment_form = CommentForm(request.POST, request.FILES)
        if not comment_form.is_valid():
            return self.render_to_response(self.get_context_data(form=comment_form))

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

        for f in files:
            TicketAttachment.objects.create(comment=comment, file=f)

        if self.is_staff_user:
            try:
                _send_staff_comment_email(self.ticket, comment)
            except Exception:
                pass

        now = timezone.now()

        if self.ticket.status == Ticket.Status.CLOSED:
            # Only a student comment can reopen a closed ticket.
            # Staff cannot comment on closed tickets (guarded by the 'assigned_to' check above).
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

    def post_action_add_internal_note(self, request, *args, **kwargs):
        """Save a staff-only internal note.
        Raises Http404 for students.
        """
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
        """
        Mark the ticket CLOSED/ANSWERED.
        'update_fields' bypasses 'clean()', so closure fields must be set explicitly here.
        """
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
        """Reopen a closed ticket to AWAITING_STAFF."""
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

    # Context builder
    def get_context_data(self, **kwargs):
        """
        Build the template context.

        Preserves an invalid comment form from kwargs.
        Annotates each comment with 'can_edit' (author + within time window).
        Internal notes only added for staff.
        """
        context = super().get_context_data(**kwargs)
        context["ticket"] = self.ticket
        context["ticket_priority_form"] = self.get_priority_form()
        context["form"] = (
            kwargs.get("form") or kwargs.get("comment_form") or self.get_comment_form()
        )

        now = timezone.now()
        limit = timedelta(minutes=EDIT_TIME_LIMIT_MINUTES)
        comments = list(self.ticket.comments.select_related("author").all())
        for c in comments:
            # Annotate each comment with an edit-eligibility flag checked in the template.
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

        return context
