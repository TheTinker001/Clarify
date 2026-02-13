from django.contrib.auth import get_user_model
from django.core.validators import MaxLengthValidator
from django.db import models

User = get_user_model()


class Comment(models.Model):
    """Model representing a comment on a ticket."""

    BODY_MAX_LENGTH = 5000

    ticket = models.ForeignKey(
        "Ticket",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    body = models.TextField(
        max_length=BODY_MAX_LENGTH,
        validators=[MaxLengthValidator(BODY_MAX_LENGTH)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on Ticket {self.ticket_id}"

    class Meta:
        ordering = ["created_at"]
