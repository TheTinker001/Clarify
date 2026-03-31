from django.db import models
from django.core.validators import MaxLengthValidator
from django.core.exceptions import ValidationError
from tickets.models import IssueGroup
from clarify.settings import BODY_LENGTH_MAX
from django.contrib.auth import get_user_model

User = get_user_model()


class IssueUpdate(models.Model):
    """Model representing an update for an issue group."""

    issue_group = models.ForeignKey(
        IssueGroup, on_delete=models.CASCADE, related_name="issue_updates"
    )
    message = models.TextField(validators=[MaxLengthValidator(BODY_LENGTH_MAX)])
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"user_type": User.USER_TYPE_STAFF},
    )

    class Meta:
        ordering = ["-created_at", "-pk"]

    def clean(self):
        """Validate student/assigned_to types, require closed_reason when CLOSED, and clear closure fields otherwise."""
        super().clean()

        if self.created_by.user_type != User.USER_TYPE_STAFF:
            raise ValidationError(
                {"student": "Issue group message broadcast can only be made by staff."}
            )
