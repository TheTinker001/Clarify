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
    """Allow a comment author to edit their comment within 10 minutes."""

    def _get_comment_or_404(self, request, ticket_url_code, comment_url_code):
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
