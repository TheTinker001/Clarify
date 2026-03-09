from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from tickets.forms.comment_form import CommentForm
from tickets.models import Comment
from clarify.settings import EDIT_TIME_LIMIT_MINUTES


class EditCommentView(LoginRequiredMixin, View):
    """Let the comment author edit their comment within 'EDIT_TIME_LIMIT_MINUTES'."""

    def _get_comment_or_404(self, request, ticket_url_code, comment_url_code):
        """
        Return the comment, raising Http404 if the user is not the author or the edit window has expired.

        Both URL codes are used in the lookup so a user can't edit a comment on a different ticket
        by guessing the comment's URL code.
        """
        comment = get_object_or_404(
            Comment.objects.select_related("ticket"),
            url_code=comment_url_code,
            ticket__url_code=ticket_url_code,
        )

        if comment.author != request.user:
            raise Http404

        elapsed = timezone.now() - comment.created_at
        if elapsed > timedelta(minutes=EDIT_TIME_LIMIT_MINUTES):
            raise Http404

        return comment

    def get(self, request, ticket_url_code, comment_url_code):
        """Display the edit form pre-populated with the comment's current body."""
        comment = self._get_comment_or_404(request, ticket_url_code, comment_url_code)
        form = CommentForm(instance=comment)
        return render(
            request,
            "edit_comment.html",
            {
                "form": form,
                "comment": comment,
            },
        )

    def post(self, request, ticket_url_code, comment_url_code):
        """Save the edited comment.
        Re-render with errors if the form is invalid."""
        comment = self._get_comment_or_404(request, ticket_url_code, comment_url_code)
        form = CommentForm(request.POST, instance=comment)

        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been edited.")
            return redirect("ticket_detail", url_code=comment.ticket.url_code)

        return render(
            request,
            "edit_comment.html",
            {
                "form": form,
                "comment": comment,
            },
        )
