from django.db import models
from tickets.models import IssueGroup
from clarify.settings import BODY_LENGTH_MAX

from django.contrib.auth import get_user_model

User = get_user_model()


class IssueUpdate(models.Model):
    issue = models.ForeignKey(
        IssueGroup, on_delete=models.CASCADE, related_name="issue_updates"
    )
    message = models.TextField(max_length=BODY_LENGTH_MAX)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"user_type": User.USER_TYPE_STAFF},
    )

    class Meta:
        ordering = ["-created_at"]
