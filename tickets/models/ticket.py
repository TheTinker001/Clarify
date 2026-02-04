from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Ticket(models.Model):
    """Model representing a support ticket."""

    class Status(models.TextChoices):
        """Status options for a ticket."""
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In progress'
        RESOLVED = 'resolved', 'Resolved'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    story_points = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tickets',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.pk} {self.title}"
