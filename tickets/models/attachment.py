import os
from django.db import models
from django.core.validators import FileExtensionValidator
from tickets.helpers import _validate_file_size
from clarify.settings import ALLOWED_EXTENSIONS

import os


class TicketAttachment(models.Model):
    """A single file attachment, linked to either a ticket or a comment."""

    MAX_FILES_PER_TICKET = 5

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
        return os.path.basename(self.file.name)

    def __str__(self):
        return self.filename()
