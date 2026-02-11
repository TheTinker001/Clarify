from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from tickets.forms import TicketForm


def _send_ticket_created_email(ticket):
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return
    if not ticket.student.email:
        return

    subject_template = getattr(
        settings, "TICKET_CREATED_EMAIL_SUBJECT", "We received your query"
    )
    body_template = getattr(
        settings,
        "TICKET_CREATED_EMAIL_BODY",
        (
            "Hi {first_name},\n\n"
            "Your ticket has been received. We'll review it and get back to you.\n\n"
            "Ticket ID: {ticket_id}\n"
            "Subject: {subject}\n\n"
            "Thanks,\n"
            "Clarify Team"
        ),
    )
    subject = subject_template.format(
        ticket_id=ticket.pk,
        subject=ticket.subject,
        first_name=ticket.student.first_name or "there",
    )
    body = body_template.format(
        ticket_id=ticket.pk,
        subject=ticket.subject,
        first_name=ticket.student.first_name or "there",
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
        recipient_list=[ticket.student.email],
        fail_silently=False,
    )


@login_required
def create_ticket(request):
    if request.user.user_type != "student":
        return redirect("dashboard")

    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.student = request.user
            ticket.save()
            _send_ticket_created_email(ticket)
            return redirect("dashboard")
    else:
        form = TicketForm()

    return render(request, "create_ticket.html", {"form": form})
