from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from tickets.forms.ticket_priority_form import TicketPriorityForm
from tickets.forms import CommentForm, InternalNoteForm
from tickets.models import Ticket, User, InternalNote
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from tickets.models.attachment import TicketAttachment


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

        # Internal note submission
        elif action == "add_internal_note":
            return self.post_action_add_internal_note(request, *args, **kwargs)

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

            for f in files:
                TicketAttachment.objects.create(comment=comment, file=f)

            messages.success(request, "Comment added.")
            return redirect("ticket_detail", url_code=kwargs.get("url_code"))

        return self.render_to_response(self.get_context_data(form=comment_form))

    def post_action_add_internal_note(self, request, *args, **kwargs):
        if not self.is_staff_user:
            raise Http404

        note_form = InternalNoteForm(request.POST)

        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.ticket = self.ticket
            note.author = request.user
            note.save()
            messages.success(request, "Internal note added.")
            return redirect("ticket_detail", url_code=kwargs.get("url_code"))

        return self.render_to_response(self.get_context_data(internal_note_form=note_form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ticket"] = self.ticket
        context["ticket_priority_form"] = self.get_priority_form()
        context["form"] = kwargs.get("form") or self.get_comment_form()
        context["comments"] = self.ticket.comments.select_related("author").all()
        if self.is_staff_user:
            context["internal_notes"] = self.ticket.internal_notes.select_related("author").all()
            context["internal_note_form"] = kwargs.get("internal_note_form") or InternalNoteForm()
        return context
