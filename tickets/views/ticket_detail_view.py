from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from tickets.forms import CommentForm
from tickets.models import Ticket, User


@login_required
def ticket_detail(request, url_code):
    """Display a single ticket and handle comment submission."""
    ticket = get_object_or_404(
        Ticket.objects.select_related("student", "assigned_to"),
        url_code=url_code,
    )

    is_staff_user = request.user.user_type == User.USER_TYPE_STAFF
    is_owner = ticket.student_id == request.user.id

    if not (is_staff_user or is_owner):
        raise Http404

    if request.method == "POST":
        if is_staff_user and not ticket.assigned_to:
            raise Http404

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()
            return redirect("ticket_detail", url_code=url_code)
    else:
        form = CommentForm()

    comments = ticket.comments.select_related("author").all()
    return render(
        request,
        "ticket_detail.html",
        {"ticket": ticket, "form": form, "comments": comments},
    )
