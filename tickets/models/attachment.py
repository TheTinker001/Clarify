import os
from django.db import models
from django.core.validators import FileExtensionValidator
from tickets.helpers import _validate_file_size
from clarify.settings import ALLOWED_EXTENSIONS


class TicketAttachment(models.Model):
    """A file attached to either a ticket or a comment (exactly one FK should be set)."""

    ticket = models.ForeignKey(
        "Ticket",
        on_delete=models.CASCADE,
        related_name="attachments",
        null=True,
        blank=True,
    )
    comment = models.ForeignKey(
        "Comment",
        on_delete=models.CASCADE,
        related_name="attachments",
        null=True,
        blank=True,
    )
    file = models.FileField(
        upload_to="ticket_attachments/%Y/%m/%d/",
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_EXTENSIONS),
            _validate_file_size,
        ],
    )

    def filename(self):
        """Return the bare filename, stripping the upload-path prefix stored in the DB."""
        return os.path.basename(self.file.name)

    def __str__(self):
        """Return the bare filename as the string representation."""
        return self.filename()
