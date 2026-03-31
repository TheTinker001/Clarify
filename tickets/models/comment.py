import secrets
from django.urls import reverse
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Comment(models.Model):
    """Model representing a comment on a ticket."""

    class Meta:
        ordering = ["created_at"]

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
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    url_code = models.CharField(max_length=64, unique=True, blank=True, null=False)

    def save(self, *args, **kwargs):
        """
        Auto-generate a unique URL code using a cryptographically safe token before saving.
        """
        if not self.url_code:
            self.url_code = self.generate_unique_url_code()
        self.full_clean()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Return the absolute URL for this comment's edit view.
        """
        return reverse(
            "edit_comment",
            kwargs={
                "ticket_url_code": self.ticket.url_code,
                "comment_url_code": self.url_code,
            },
        )

    def generate_unique_url_code(self):
        """
        Generate a unique URL-safe token, retrying on collision.
        """
        code = secrets.token_urlsafe(7)
        while Comment.objects.filter(url_code=code).exists():
            code = secrets.token_urlsafe(7)
        return code

    def __str__(self):
        """Return a human-readable summary identifying the comment's author and ticket."""
        return f"Comment by {self.author} on Ticket {self.ticket_id}"
