from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TicketResponse(models.Model):
    """A response/message on a ticket from either staff or student."""

    ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.CASCADE,
        related_name="responses",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ticket_responses",
    )
    body = models.TextField(max_length=10000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Response by {self.author.username} on Ticket #{self.ticket_id}"
