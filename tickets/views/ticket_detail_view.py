from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from tickets.forms.ticket_priority_form import TicketPriorityForm
from tickets.forms import CommentForm
from tickets.models import Ticket, User


@login_required
def ticket_detail(request, url_code):
    """Display a single ticket and handle priority and handle comment submission."""
    ticket = get_object_or_404(
        Ticket.objects.select_related("student", "assigned_to"),
        url_code=url_code,
    )

    is_staff_user = request.user.user_type == User.USER_TYPE_STAFF
    is_owner = ticket.student_id == request.user.id

    # Permission check
    if not (is_staff_user or is_owner):
        raise Http404

    # Default forms for GET
    if is_staff_user:
        priority_form = TicketPriorityForm(instance=ticket)
    else:
        priority_form = None

    comment_form = CommentForm()

    if request.method == "POST":
        action = request.POST.get("action")

        # Priority update
        if action == "set_priority":
            if not is_staff_user:
                raise Http404
            if ticket.status == Ticket.Status.CLOSED:
                raise Http404

            priority_form = TicketPriorityForm(request.POST, instance=ticket)
            if priority_form.is_valid():
                priority_form.save()
                messages.success(request, "Priority updated.")
            else:
                messages.error(request, "Invalid priority.")

            return redirect("ticket_detail", url_code=url_code)

        # Comment submission
        elif action == "add_comment":
            if is_staff_user and ticket.assigned_to_id != request.user.id:
                raise Http404

            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.ticket = ticket
                comment.author = request.user
                comment.save()
                messages.success(request, "Comment added.")
                return redirect("ticket_detail", url_code=url_code)

        else:
            raise Http404

    comments = ticket.comments.select_related("author").all()

    return render(
        request,
        "ticket_detail.html",
        {
            "ticket": ticket,
            "ticket_priority_form": priority_form,
            "form": comment_form,
            "comments": comments,
        },
    )
