from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from tickets.forms import TicketForm


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
            return redirect("dashboard")
    else:
        form = TicketForm()

    return render(request, "create_ticket.html", {"form": form})
